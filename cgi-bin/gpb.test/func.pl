use utf8; use Encode; use open ':utf8'; binmode STDOUT, ":encoding(UTF-8)";
use Time::Local;
use JSON;

require 'config.pl';  # # Конфиг и окружение


# # # # # # # # # # # # # # # # # # # # # # # # # # # # #



#		 ПОЛУЧЕНИЕ ВВОДА





#				и обработка
#
# на входе 		my %inp = GetInput();
#
# на выходе hash %inpt
#
#	#	#	#	#	#	#	#	#	#	#	#	#	#	#

sub GetInput {
			my %inpt;
			my $input = '';

	# Определение источника ввода
			if ($ENV{'QUERY_STRING'}) {
				$input = $ENV{'QUERY_STRING'};
			} elsif ($ENV{'CONTENT_LENGTH'}) {
				read(STDIN, $input, $ENV{'CONTENT_LENGTH'});
			}

			#### подпрограммы для раскодировки utf8 символов, закодированных в url
					 sub u8from_url {
						 $hexstr1='0x'.$_[0]; $hexstr2='0x'.$_[1];
							$dec_code_utf8 = (hex($hexstr1)-193)*64-64+hex($hexstr2); # формула раскодировки utf8 символов, закодированных в url (hex($hexstr1)-193)*64-64+hex($hexstr2)
						chr($dec_code_utf8);
					 }
					 sub u88from_url {
						 $hexstr1='0x'.$_[0]; $hexstr2='0x'.$_[1]; $hexstr3='0x'.$_[2];
							$dec_code_utf8 = (hex($hexstr1)-223)*64*64-(64*64)+((hex($hexstr2)-127)*64)-64+hex($hexstr3)-128; # формула раскодировки utf8 символов, закодированных в url
						chr($dec_code_utf8);
					 }
					 sub u888from_url {
						 $hexstr1='0x'.$_[0]; $hexstr2='0x'.$_[1]; $hexstr3='0x'.$_[2]; $hexstr4='0x'.$_[3];
							$dec_code_utf8 = (hex($hexstr1)-239)*64*64*64-(64*64*64)+(hex($hexstr2)-127)*64*64-(64*64)+(hex($hexstr3)-127)*64-64+hex($hexstr4)-128; # формула раскодировки utf8 символов, закодированных в url
						chr($dec_code_utf8); # return $dec_code_utf8;
					 }

	# Разбор по парам ключ-значение и обработка воода
			my $name = '';
			my $value = '';
			my $pair = '';
			my @pairs = split(/&/, $input);
			foreach $pair (@pairs)
			{
				($name, $value) = split(/=/, $pair);
				$inpt{$name} = $value;
				$inpt{$name}=~ s/\+/ /g;
				$inpt{$name} =~ s/%([fF][0-9a-fA-F])%([8-9a-bA-B][0-9a-fA-F])%([8-9a-bA-B][0-9a-fA-F])%([8-9a-bA-B][0-9a-fA-F])/u888from_url($1, $2, $3, $4)/ge; # раскодируются юникодные заэскейпленные коды
				$inpt{$name} =~ s/%([eE][0-9a-fA-F])%([8-9a-bA-B][0-9a-fA-F])%([8-9a-bA-B][0-9a-fA-F])/u88from_url($1, $2, $3)/ge;
				$inpt{$name} =~ s/%([c-dC-D][0-9a-fA-F])%([8-9a-bA-B][0-9a-fA-F])/u8from_url($1, $2)/ge; 
				$inpt{$name}=~ s/%([0-9A-Fa-f][0-9A-Fa-f])/chr hex $1/ge; 
			}
		return %inpt;
}


# # # # # # # # # # # # # # # # # # # # # # # # # # # # #



#		 КОНВЕРТАЦИЯ ДАТЫ В UNIX TIMESTAMP





#				
#
# на входе 		my $tmstamp = txt2timestamp('datm'=>'2012-02-13 15:09:31');
#
# на выходе epoch (timestamp)
#
#	#	#	#	#	#	#	#	#	#	#	#	#	#	#

				sub txt2timestamp {
					my (%hprm) = @_;
						my $rezult=0;
						my $actaccept=1;
						$hprm{'datm'} =~ s/\-/ /gi;
						$hprm{'datm'} =~ s/\:/ /gi;
						if (index($hprm{'datm'},' ')>-1){
								my @ddt = split(/ /, $hprm{'datm'});
								my $dmd = int($ddt[2]);
								my $dmm = int($ddt[1]) - 1;
								my $dmy = int($ddt[0]);
								my $tms = int($ddt[5]);
								my $tmm = int($ddt[4]);
								my $tmh = int($ddt[3]);
							unless ($tms>-1 && $tms<60){	$actaccept=0;	}
							unless ($tmm>-1 && $tmm<60){	$actaccept=0;	}
							unless ($tmh>-1 && $tmh<25){	$actaccept=0;	}
							unless ($dmd>-1 && $dmd<32){	$actaccept=0;	}
							unless ($dmm>-1 && $dmm<13){	$actaccept=0;	}
							unless ($dmy>0 && $dmy<2200){	$actaccept=0;	}
							if ($actaccept>0){
								$rezult=timegm($tms,$tmm,$tmh,$dmd,$dmm,$dmy);
							}
						}
						return $rezult;
				}


#	#	#	#	#	#	#	#	#	#	#	#	#	#	#


#		 ВЫВОД РЕЗУЛЬТАТОВ ВО ФРОНТЕНД


#		подробности
#
# на входе &Output2web('outitle'=>$outputTITLE,'outhtml'=>$outputHTML,'outjson'=>$outputJSON,'outerr'=>$outputERR);
#						$inparam{'outitle'}	- заголовок для вывода результатов
#						$inparam{'outhtml'}	- контейнер для вывода результатов в виде HTML
#						$inparam{'outjson'}	- контейнер для вывода результатов в виде JSON
#						$inparam{'outerr'}	- контейнер для сбора ошибок
# на выходе 
#
#	#	#	#	#	#	#	#	#	#	#	#	#	#	#

sub Output2web {
	my %envcfg = EnvConfig();	# Загрузка конфига и окружения
		my (%inparam) = @_;

	# заголовки вывода
							print 'Content-Type: text/html; charset=utf-8'."\n";
							print 'X-Content-Type-Options: nosniff'."\n";
							print 'Cache-Control: no-cache'."\n";
									# куки не нужны
							print "\n"; # конец заголовков

					if (length($inparam{'outhtml'}) > 1) {
	# загрузка шаблона вывода в формате HTML
							my $HTMLtemplate='';
							open(FLO, $envcfg{'path'}.'template4cgi.html') || die 'bad file '.$envcfg{'path'}.'template4cgi.html opening';
								flock (FLO,1);
								while(<FLO>) { $HTMLtemplate .= $_;}
							close FLO;
						if ($HTMLtemplate =~ /XXXXcontentXXXX/si) {
							$HTMLtemplate =~ s/XXXXtitleXXXX/$inparam{'outitle'}/gi;
							$HTMLtemplate =~ s/XXXXcontentXXXX/$inparam{'outhtml'}/gi;
							$HTMLtemplate =~ s/XXXXjsonXXXX/$inparam{'outjson'}/gi;
															$Mistake2userID .= '';	# конвертнули интегер в стринг
							$HTMLtemplate =~ s/XXXXmistakeXXXX/$Mistake2userID/gi;	# сообщение для пользователя о текущей ошибке
						} else {
							&erlog('lib' => 'func', 'ertyp' => 'BadTemplateHtml', 'val' => '-', 'va2' => '-', 'va3' => '-', 'va4' => '-');
						}
							print $HTMLtemplate;
					} elsif (length($inparam{'outjson'}) > 5) {
	# вывод только JSON
							print $inparam{'outjson'};
					} else {
							&erlog('lib' => 'func', 'ertyp' => 'EmptyOutput', 'val' => '-', 'va2' => '-', 'va3' => '-', 'va4' => '-');
					}
	return 1;
}

#	#	#	#	#	#	#	#	#	#	#	#	#	#	#


#		СБОР ОШИБОК


#		подробности
#
# на входе &erlog('lib' => 'scriptname', 'ertyp' => 'ErrorDescription', 'val' => '-', 'va2' => '-', 'va3' => '-', 'va4' => '-');
#						
# на выходе кастомный errors.log	(время, ip, скрипт, ошибка, 4 переменных с деталями)
#
#	#	#	#	#	#	#	#	#	#	#	#	#	#	#


sub erlog {
	my %envcfg = EnvConfig();	# Загрузка конфига и окружения
		my (%inparam) = @_;
			open(SAVV, '>>'.$envcfg{'path'}.'errors.log') || die 'bad file '.$envcfg{'path'}.'errors.log opening';
				flock (SAVV,2);
					print SAVV "\n" . time() . "\t" . $ENV{'REMOTE_ADDR'}. "\t" . $inparam{'lib'} . "\t" . $inparam{'ertyp'} . "\t\"" . $inparam{'val'} . "\"\t\"". $inparam{'va2'} . "\"\t\"". $inparam{'va3'} . "\"\t\"". $inparam{'va4'} . "\"";
			close(SAVV);	
		return 1;
}
return 1;

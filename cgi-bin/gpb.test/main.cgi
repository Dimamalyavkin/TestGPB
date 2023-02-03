#!/usr/bin/perl
#use strict;
use warnings;
use utf8; use Encode; use open ':utf8';
use JSON;
use DBI;

#	#	#	#	#	#	#	#	#	#	#	#	#	#	#


#		ГЛАВНЫЙ СКРИПТ ПО ТЕСТОВОМУ ЗАДАНИЮ


#		создание новой SQL базы, парсинг log-файла, вывод результатов поиска
#
# на входе
#			логфайл 'out', который лежит в папке $envcfg{'path'}
#			&addrs=text (optional) фрагмент текста или полный адрес почты, по которому делается выборка из базы
#
# на выходе 
#			заполненный шаблон $envcfg{'path'}.'template4cgi.html'
#
#	#	#	#	#	#	#	#	#	#	#	#	#	#	#

#		ЗАМЕЧАНИЯ ПО ЗАДАНИЮ
#	* не понятен формат строки TIMESTAMP(0) в задании, там же должно быть 4 байта без вариантов
#	* тайм зоны - в задании не актуально, т.к. исходные данные берутся из фиксированного лога и нет согласования с выводом во фронтенд
#	* VARCHAR в моей тестовой MySQL 5.7 требует указания лимита, ограничил в 255 символа для ID, в 319 для ADDRESS, а для STR - 1024
#	* BOOLEAN в MySQL автоматом конвертится в tinyint
#	* в логе есть 360 строк, которые по заданию нельзя занести в базу данных, т.к. в них есть флаг прибытия '<=', но нет присвоенного 'id=', который является обязательным полем (NOT NULL), пример:
#			2012-02-13 14:39:22 1RwtJa-000AFJ-3B <= <> R=1RookS-000Pg8-VO U=mailnull P=local S=3958
#



require 'config.pl';  # # Конфиг и окружение
	my %envcfg = EnvConfig();	# Загрузка конфига и окружения

require 'func.pl';  # Вывод результатов во фронтенд
	my $outputTITLE='Test GPB'; # заголовок для вывода результатов
	my $outputHTML='   '; # контейнер для вывода результатов в виде HTML
	my $outputJSON='{}'; # контейнер для вывода результатов в виде JSON
	my $outputERR=''; # контейнер для сбора ошибок


my $dbhandl = DBI->connect($envcfg{'dbaccess'},$envcfg{'dblogin'},$envcfg{'dbpwd'}) || die("Error connecting to the database");
# протестировано на MySQL 5.7

				my $dbqu = $dbhandl->prepare('SHOW TABLES LIKE ?');
				$dbqu->execute('message');
				my @isdb = $dbqu->fetchrow_array();
				$dbqu->finish();

# создание таблиц в базе данных (если их до этого еще не создали)
			if ($#isdb<0){
				my @dbNewTbls = (
							"create table if not exists message(
								created timestamp not null,
								id varchar(255) primary key not null,
								int_id char(16) not null,
								str varchar(1024) not null,
								status boolean
							);",
							"create index message_created_idx ON message (created);",
							"create index message_int_id_idx ON message (int_id);",
							"create table if not exists log(
								created timestamp not null,
								int_id char(16) not null,
								str varchar(1024),
								address varchar(319)
							);",
							"create index log_address_idx ON log (address);"
				);

					for my $ix (0 .. $#dbNewTbls){
							$dbhandl->do($dbNewTbls[$ix]);
					}
					@isdb = ['message','log']; # соозданы базы
			}

# здесь должна была бы быть вменяемая проверка последнего обновления базы данных, чтобы повтороно не заливать туда инфу, но т.к. формат и версионность не согласована ограничусь простейшей заплаткой
			my $dblogfile='out';
			unless (-e $envcfg{'path'}.$dblogfile.'.done'){

# открытие лога с данными для заброски его в базу
				if (-e $envcfg{'path'}.$dblogfile) {
					my @etalon = split(/ /, $envcfg{'logformat'});	# заголовки полей строки лога
					if ($#etalon>4){
						my $etahash = {};
							for my $ix (0 .. $#etalon){
								if (length($etalon[$ix])>1){
									$etahash{$etalon[$ix]}=$ix;
								}
							}
						my @etacheck = split(/ /, 'date time int_id flag address');	# проверка всех необходимых полей в формате лога
						my $etachecker = 0;
							for my $ix (0 .. $#etacheck){
								if ($etahash{$etacheck[$ix]} > -1){
									$etachecker ++;
								}
							}
						if ($etachecker > 4) {
							my $readline='';
								my $dbquM = $dbhandl->prepare('INSERT INTO message(created,id,int_id,str) VALUES(?,?,?,?)');		# подготовлен шаблон добавления в базу message
								my $dbquL = $dbhandl->prepare('INSERT INTO log(created,int_id,str,address) VALUES(?,?,?,?)'); 		# подготовлен шаблон добавления в базу log
							open FLIN, $envcfg{'path'}.'out'; 
								flock (FLIN,1); 
								while(<FLIN>) { 
									$readline=$_;
										if (length($readline)>10){						# проверка наличия смысла в строке
											$readline =~ s/\n//g;
											$readline =~ s/\r//g;
											$readline =~ s/\t//g;
											my @templine = split(/ /, $readline);
											if ($#templine>2){							# в строке может быть дата
												my $inlogID = '';
												my $tmstamp = txt2timestamp('datm'=>$templine[$etahash{'date'}].' '.$templine[$etahash{'time'}]);
													my $tmstampformat=$templine[$etahash{'date'}].' '.$templine[$etahash{'time'}];
												if ($tmstamp>10000 && length($templine[$etahash{'int_id'}]) > 1){		# строка минимально валидная
													my $logWOdate=$templine[2];
													for my $ix (3 .. $#templine){			# собрали строку лога без даты
															$logWOdate.=' '.$templine[$ix];
															if (index($templine[$ix],'id=') > -1){
																(my $idid, $inlogID) = split(/\=/, $templine[$ix]);
															}
													}
													my $tologdb=0;
													if ($#templine > $etahash{'flag'}){
														if ($templine[$etahash{'flag'}] eq '<=' && $inlogID ne '' && length($templine[$etahash{'int_id'}])>0 && length($logWOdate)>0){

															$dbquM->execute($tmstampformat,$inlogID,$templine[$etahash{'int_id'}],$logWOdate);	# закинули в базу message по шаблону

														} elsif ($templine[$etahash{'flag'}] ne '<='){
															$tologdb=1;
														} else {
															&erlog('lib' => 'main', 'ertyp' => 'hmmm', 'val' => $templine[$etahash{'int_id'}], 'va2' => $readline, 'va3' => '-', 'va4' => '-');
														}
													} else {
															$tologdb=1;
													}
													if ($tologdb > 0){
														my $validEmail='';
															if ($#templine > $etahash{'address'}){
																if ($templine[$etahash{'address'}] =~ /^[0-9a-zA-Z]+\@[-0-9a-zA-Z._]+$/){		# валидация почтового адреса
																	$validEmail = $templine[$etahash{'address'}];
																} elsif ($templine[$etahash{'address'}] =~ /^[0-9a-zA-Z][-0-9a-zA-Z._]+\@[-0-9a-zA-Z._]+$/){
																	$validEmail = $templine[$etahash{'address'}];
																}
															}

															$dbquL->execute($tmstampformat,$templine[$etahash{'int_id'}],$logWOdate,$validEmail);	# закинули в базу log по шаблону

													}
												} else {
													&erlog('lib' => 'main', 'ertyp' => 'WRONGlogFormat', 'val' => $readline, 'va2' => $tmstampformat, 'va3' => $templine[$etahash{'int_id'}], 'va4' => $templine[$etahash{'date'}].' '.$templine[$etahash{'time'}]);
												}
											} else {
												&erlog('lib' => 'main', 'ertyp' => 'EMPTYlogLINE', 'val' => $readline);
											}
										}
								}
							close FLIN;
							# создается файлик, свидетельствующий о том, что эти данные в базу уже загружены - защита от дублирующего добавления данных в базу
												open(SAVV, '>'.$envcfg{'path'}.$dblogfile.'.done') || die "bad file opening";
													flock (SAVV,2);
														print SAVV "Prevent this data from doubles"; 
												close(SAVV);
							$dbquM->finish();	# закрыли шаблоны добавления в базу
							$dbquL->finish();
						} else {
							$Mistake2userID=3;	# ошибка - в конфиге задан не полный формат лога
						}
					} else {
						$Mistake2userID=2;	# ошибка - не указан формат данных в логе
					}
				} else {
						$Mistake2userID=1;	# ошибка - отсутствует файл с данными
				}
			}
				# проверка на наличие баз данных
			if ($#isdb > -1){
				my %inp = GetInput();

# вытаскиваем из базы все int_id к которым имеет отношение искомый address
					if (length($inp{'addrs'}) > 4){
						my $quintid='SELECT created,int_id,address FROM `log` WHERE address like '."\'\%".$inp{'addrs'}."\%\' ORDER BY created\;";
						my $dbquP = $dbhandl->prepare($quintid);
						$dbquP->execute();
						my $intidlimiter=0;
						my $intids={};
						while(my @row = $dbquP->fetchrow_array()){
							if ($intidlimiter < 101){
								unless ($intids{$row[1]}){
									$intidlimiter++;			# смотрим, чтобы за сотню перевалило максимум на одну позицию
									$intids{$row[1]} = $row[2];
								}
							}
						}
						$dbquP->finish();

# вытаскиваем из базы все логи по отобранному перечню int_id
						if ($intidlimiter > 0){
							my $qufinal='';
							my $orcount = 0;
							my @finalist;

							foreach my $key (keys(%intids)) {
								if ($orcount > 0) {
									$qufinal .= ' or int_id = '."\'".$key."\'";
								} else {
									$qufinal .= ' int_id = '."\'".$key."\'";
								}
									$orcount ++;
							}
									$qufinal .= ' ORDER BY created;';
							$intidlimiter=0;
							my $dbquF = $dbhandl->prepare('SELECT created,int_id,str FROM log WHERE'.$qufinal);
									$dbquF->execute();
									while(my @row = $dbquF->fetchrow_array()){
										if ($intidlimiter < 101){
											$intidlimiter++;			# смотрим, чтобы за сотню перевалило максимум на одну позицию
											push(@finalist, $row[0]."\t".$row[1]."\t".$row[2]);
										}
									}
							$dbquF->finish();
							
							$intidlimiter=0;
							my $dbquFF = $dbhandl->prepare('SELECT created,int_id,str FROM message WHERE'.$qufinal);
									$dbquFF->execute();
									while(my @row = $dbquFF->fetchrow_array()){
										if ($intidlimiter < 101){
											$intidlimiter++;			# смотрим, чтобы за сотню перевалило максимум на одну позицию
											push(@finalist, $row[0]."\t".$row[1]."\t".$row[2]);
										}
									}
							$dbquFF->finish();

# форматирование вывода (по хорошему, его надо в JSON выводить, но по заданию не фронтенд оценивается, поэтому по старинке - форматирование через perl)
							my @sortedfinalist = sort @finalist;
							if ($#finalist > 100){
								$Mistake2userID=7;	# сообщение - выведено только первые 100 результатов из большего количества
							}
							my $fintids={};
							$intidlimiter=0;
							for my $ix (0 .. $#sortedfinalist){
								if ($intidlimiter < 100){
									my @row = split(/\t/, $sortedfinalist[$ix]);
										$intidlimiter++;			# смотрим, чтобы за сотню не перевалило
									unless ($fintids{$row[1]}){
										$fintids{$row[1]}='';
									}
										$fintids{$row[1]}.='<p class="lin">'.$row[0].' '.$row[2].'</p>';
								}
							}
							$intidlimiter=0;
							for my $ix (0 .. $#sortedfinalist){
								if ($intidlimiter < 100){
									my @row = split(/\t/, $sortedfinalist[$ix]);
										$intidlimiter++;
									if ($intids{$row[1]} ne ''){
										$outputHTML .= '<H2>'.$row[1].'</H2><i>'.$intids{$row[1]}.'</i>'.$fintids{$row[1]}."\n";
										$intids{$row[1]} = '';
									}
								}
							}
						} else {
							$Mistake2userID=6;	# ошибка - нет совпадающих с запросом данных
						}
					} elsif ($Mistake2userID < 1) {
						$Mistake2userID=5;	# ошибка - запрос отсутствует или слишком короткий
					}
			} elsif ($Mistake2userID < 1) {
					$Mistake2userID=4;	# ошибка - в базу не загружены данные
			}

$dbhandl->disconnect();

&Output2web('outitle'=>$outputTITLE,'outhtml'=>$outputHTML,'outjson'=>$outputJSON,'outerr'=>$outputERR); # Вывод результатов во фронтенд

exit;




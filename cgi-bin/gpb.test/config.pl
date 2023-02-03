use utf8; use Encode; use open ':utf8'; binmode STDOUT, ":encoding(UTF-8)";


# # # # # # # # # # # # # # # # # # # # # # # # # # # # #



#		 КОНФИГ И ОКРУЖЕНИЕ





#				пути и прочие аксиомы
#
# на входе 		my %envcfg = EnvConfig();
#
# на выходе hash %envcfg
#
#	#	#	#	#	#	#	#	#	#	#	#	#	#	#

		# глобальная собиралка ошибок для извещения юзера
				$Mistake2userID=0;

sub EnvConfig {
		my %envcfg;
					# путь к данным
			$envcfg{'path'}='../../gpb.test/';
			$envcfg{'logformat'}='date time int_id flag address other';
					# доступ к базе данных my $dbhandl = DBI->connect($envcfg{'dbaccess'},$envcfg{'dblogin'},$envcfg{'dbpwd'}) || die("Error connecting to the database");
			$envcfg{'dbaccess'}='DBI:mysql:host1778366_gpb:localhost';
			$envcfg{'dbname'}='host1778366_gpb';
			$envcfg{'dblogin'}='host1778366_gpbuser';
			$envcfg{'dbpwd'}='Gazpr0mbank';
		return %envcfg;
}
return 1;


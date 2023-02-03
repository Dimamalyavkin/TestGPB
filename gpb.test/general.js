						
	function erlog(elib,etyp,errval1,errval2) {		// optional param errval1,errval2
		alert('&elib=' + elib + '&etyp=' + etyp + '&eval1=' + eval1 + '&eval2=' + eval2);
	}

// ЯЗЫКОВОЙ ФАЙЛ (упрощенный) - - - - - 
		var mistakMSG=[
					'неизвестная ошибка',
					'Ошибка 1: отсутствует файл за данными',
					'Ошибка 2: не указан формат данных в логе',
					'Ошибка 3: в конфиге задан не полный формат лога',
					'Ошибка 4: в базу не загружены данные',
					'Ошибка 5: запрос отсутствует или слишком короткий',
					'Ошибка 6: нет совпадающих с запросом данных',
					'Сообщение 7: выведено только первые 100 результатов из большего количества',
					'текст ошибки',
					'крайняя ошибка'
			];

// Вывод ошибки или сообщения от сервера - - - - - 
	function checkMistake(){
		var mistid=parseInt(mistakeMSGid);
		if (mistid > 0){
			if (!(mistid < mistakMSG.length)){
				mistid=0;
			}
			document.getElementById('mistamsg').innerHTML = mistakMSG[mistid];
			document.getElementById('mistake').style.display='block';
		}
	}

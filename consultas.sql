USE CertiGest;
select * from evento;

select * from asistente;

select * from asistencia ;

select * from asistencia WHERE DNI="72645478";

SELECT CODIGO, TITULO, DATE_FORMAT(FECHA, '%d-%m-%Y') AS FECHA FROM EVENTO;

select * from asistencia WHERE id_evento="2";

select * from CARRERA;


delete from evento where id=1;
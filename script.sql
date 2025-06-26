	DROP DATABASE CERTIGEST;
    CREATE DATABASE CertiGest;
    USE CertiGest;
	    
	CREATE TABLE CARRERA (
		ID CHAR(2) PRIMARY KEY NOT NULL,
		NOMBRE VARCHAR(40) NOT NULL
	);

	CREATE TABLE ASISTENTE (
		DNI CHAR(8) PRIMARY KEY NOT NULL,
		APELLIDOS VARCHAR(60) NOT NULL,
		NOMBRES VARCHAR(60) NOT NULL,
		ID_CARRERA CHAR(2) NOT NULL,
		CORREO VARCHAR(40) NOT NULL,
		SEMESTRE VARCHAR(8) NOT NULL,
		CONSTRAINT fk_asistente_carrera 
			FOREIGN KEY (ID_CARRERA) REFERENCES CARRERA(ID)
			ON UPDATE CASCADE
			ON DELETE RESTRICT
	);

	CREATE TABLE EVENTO (
		CODIGO VARCHAR(10) UNIQUE NOT NULL,
		TITULO VARCHAR(70) NOT NULL,
		IMAGEN LONGBLOB NULL,
        TIPO ENUM('EVENTO', 'TALLER') NOT NULL DEFAULT 'EVENTO',
		FECHA TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	CREATE TABLE ASISTENCIA (
		DNI CHAR(8) NOT NULL,
		CODIGO_EVENTO VARCHAR(10) NOT NULL,
		ASISTIO BOOLEAN NOT NULL, 
		CONSTRAINT pk_asistencia PRIMARY KEY (DNI, CODIGO_EVENTO),
		CONSTRAINT fk_asistencia_asistente 
			FOREIGN KEY (DNI) REFERENCES ASISTENTE(DNI)
			ON UPDATE CASCADE
			ON DELETE CASCADE,
		CONSTRAINT fk_asistencia_evento 
			FOREIGN KEY (CODIGO_EVENTO) REFERENCES EVENTO(CODIGO)
			ON UPDATE CASCADE
			ON DELETE CASCADE
	);
    
-- Validar Correo 
DELIMITER //
CREATE FUNCTION es_correo_valido(correo VARCHAR(100)) RETURNS BOOLEAN
DETERMINISTIC
BEGIN
  RETURN correo REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$';
END;
//
DELIMITER ;

-- Validar solo letras (Apellidos,Nombres)
DELIMITER //
CREATE FUNCTION solo_letras(texto VARCHAR(100)) RETURNS BOOLEAN
DETERMINISTIC
BEGIN
  RETURN texto REGEXP '^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$';
END;
//
DELIMITER ;

-- Validar DNI
DELIMITER //
CREATE FUNCTION dni_valido(dni CHAR(8)) RETURNS BOOLEAN
DETERMINISTIC
BEGIN
  RETURN dni REGEXP '^[0-9]{8}$';
END;
//
DELIMITER ;

-- Validar rango de carrera
DELIMITER //
CREATE FUNCTION carrera_valida(id_carrera CHAR(2)) RETURNS BOOLEAN
DETERMINISTIC
BEGIN
  DECLARE num_carrera INT;
  SET num_carrera = CAST(id_carrera AS UNSIGNED);
  RETURN num_carrera BETWEEN 1 AND 34;
END;
//
DELIMITER ;

-- Insertar asistente
DELIMITER //
CREATE PROCEDURE insertar_asistente(
  IN p_dni CHAR(8),
  IN p_apellidos VARCHAR(50),
  IN p_nombres VARCHAR(50),
  IN p_id_carrera CHAR(2),
  IN p_correo VARCHAR(100),
  IN p_semestre VARCHAR(8)
)
BEGIN
  IF NOT dni_valido(p_dni) THEN
	SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'DNI inválido: debe tener 8 dígitos numéricos';
  ELSEIF NOT solo_letras(p_apellidos) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Apellidos inválidos: solo letras permitidas';
  ELSEIF NOT solo_letras(p_nombres) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Nombres inválidos: solo letras permitidas';
  ELSEIF NOT carrera_valida(p_id_carrera) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Carrera inválida: debe estar entre 01 y 34';
  ELSEIF NOT es_correo_valido(p_correo) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Correo inválido';
  ELSE
    INSERT INTO ASISTENTE(DNI, APELLIDOS, NOMBRES, ID_CARRERA, CORREO, SEMESTRE)
    VALUES(p_dni, p_apellidos, p_nombres, p_id_carrera, p_correo, p_semestre);
  END IF;
END;
//
DELIMITER ;

-- Insertar Evento
DELIMITER //
CREATE PROCEDURE insertar_evento(
  IN p_titulo VARCHAR(70),
  IN p_imagen LONGBLOB,
  IN p_tipo ENUM('EVENTO', 'TALLER'),
  OUT p_codigo_generado VARCHAR(10)
)
BEGIN
  DECLARE prefijo CHAR(1);
  DECLARE ultimo_codigo INT;
  DECLARE nuevo_codigo VARCHAR(10);

  IF p_titulo IS NULL OR TRIM(p_titulo) = '' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El título del evento no puede estar vacío';
  ELSEIF p_imagen IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La imagen del evento no puede estar vacía';
  ELSE
    SET prefijo = IF(p_tipo = 'EVENTO', 'E', 'T');

    SELECT IFNULL(MAX(CAST(SUBSTRING(CODIGO, 2) AS UNSIGNED)), 0)
    INTO ultimo_codigo
    FROM EVENTO
    WHERE TIPO = p_tipo;

    SET nuevo_codigo = CONCAT(prefijo, LPAD(ultimo_codigo + 1, 3, '0'));

    INSERT INTO EVENTO(TITULO, IMAGEN, TIPO, CODIGO) 
    VALUES(p_titulo, p_imagen, p_tipo, nuevo_codigo);

    SET p_codigo_generado = nuevo_codigo;
  END IF;
END;
//
DELIMITER ;

-- Insertar asistencia 
DELIMITER //
CREATE PROCEDURE insertar_asistencia(
  IN p_dni CHAR(8),
  IN p_codigo_evento VARCHAR(10),
  IN p_asistio BOOLEAN
)
BEGIN
  DECLARE existe_asistente INT;
  DECLARE existe_evento INT;

  IF NOT dni_valido(p_dni) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'DNI inválido: debe tener 8 dígitos numéricos';
  ELSEIF p_asistio NOT IN (0, 1) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Valor de ASISTIO inválido: debe ser 0 o 1';
  ELSE
    SELECT COUNT(*) INTO existe_asistente FROM ASISTENTE WHERE DNI = p_dni;
    SELECT COUNT(*) INTO existe_evento FROM EVENTO WHERE CODIGO = p_codigo_evento;

    IF existe_asistente = 0 THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El DNI no corresponde a ningún asistente registrado';
    ELSEIF existe_evento = 0 THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El codigo del evento no existe';
    ELSE
      INSERT INTO ASISTENCIA(DNI, CODIGO_EVENTO, ASISTIO)
      VALUES(p_dni, p_codigo_evento, p_asistio);
    END IF;
  END IF;
END;
//
DELIMITER ;

DELIMITER //
CREATE PROCEDURE cargar_eventos()
BEGIN 
	SELECT CODIGO, TITULO, DATE_FORMAT(FECHA, '%d-%m-%Y') AS FECHA FROM EVENTO;
END;
//
DELIMITER ;

INSERT INTO CARRERA (ID, NOMBRE) VALUES
('01', 'COMUNICACIÓN SOCIAL'),
('02', 'EDUCACIÓN SOCIAL'),
('03', 'EDUCACIÓN PRIMARIA'),
('04', 'EDUCACIÓN SECUNDARIA'),
('05', 'PSICOLOGÍA'),
('06', 'PUBLICIDAD Y MULTIMEDIA'),
('07', 'TEOLOGÍA'),
('08', 'TRABAJO SOCIAL'),
('09', 'TURISMO Y HOTELERÍA'),
('10', 'ADMINISTRACIÓN DE EMPRESAS'),
('11', 'CIENCIA POLÍTICVA Y GOBIERNO'),
('12', 'CONTABILIDAD'),
('13', 'DERECHO'),
('14', 'INGENIERÍA COMERCIAL'),
('15', 'ARQUITECTURA'),
('16', 'INGENIERÓA AGRONÓMICA Y AGRÍCOLA'),
('17', 'INGENIERÍA AMBIENTAL'),
('18', 'INGENIERÍA CIVIL'),
('19', 'INGENIERÍA DE INDUSTRIA ALIMENTARIA'),
('20', 'INGENIERÍA DE MINAS'),
('21', 'INGENIERÍA DE SISTEMAS'),
('22', 'INGENIERÍA ELECTRÓNICA'),
('23', 'INGENIERÍA INDUSTRIAL'),
('24', 'INGENIERÍA MECÁNICA'),
('25', 'INGENIERÍA MECÁNICA ELÉCTRICA'),
('26', 'INGENIERÍA MECATRÓNICA'),
('27', 'MEDICINA VETERINARIA Y ZOOTECNIA'),
('28', 'ENFERMERÍA'),
('29', 'FARMACIA Y BIOQUÍMICA'),
('30', 'INGENIERÍA BIOTECNOLÓGICA'),
('31', 'MEDICINA HUMANA'),
('32', 'OBSTRETICIA Y PUERICULTURA'),
('33', 'ODONTOLOGÍA'),
('34', 'TECNOLOGÍA MÉDICA');
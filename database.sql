
SET NAMES utf8mb4;
-- Precaución: reinicia la base de datos completa en entorno de desarrollo
DROP DATABASE IF EXISTS tecnocontrol_escolar;
CREATE DATABASE tecnocontrol_escolar CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tecnocontrol_escolar;

-- 1. CATALOGO DE ROLES (recibe datos desde "Insercion de roles" en semilladml)
CREATE TABLE roles (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    codigo_rol VARCHAR(30) NOT NULL UNIQUE,
    nombre_actor VARCHAR(40) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- 2. CATALOGO DE PERIODOS ESCOLARES (recibe datos desde "Inserccion de periodos_escolares" en semilladml)
CREATE TABLE periodos_escolares (
    id_periodo INT AUTO_INCREMENT PRIMARY KEY,
    anio SMALLINT NOT NULL,
    ciclo ENUM('Enero-Junio', 'Agosto-Diciembre') NOT NULL,
    es_actual TINYINT(1) NOT NULL DEFAULT 0,
    actual_unico TINYINT AS (IF(es_actual = 1, 1, NULL)) PERSISTENT,
    CONSTRAINT uq_anio_ciclo UNIQUE (anio, ciclo),
    CONSTRAINT uq_periodo_actual UNIQUE (actual_unico),
    CONSTRAINT ck_periodo_es_actual CHECK (es_actual IN (0, 1))
) ENGINE=InnoDB;

-- 3. CATALOGO DE BLOQUES HORARIOS(recibe datos desde "Inserccion de tabla bloques_horarios" en semilladml)
CREATE TABLE bloques_horarios (
    id_bloque INT AUTO_INCREMENT PRIMARY KEY,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    etiqueta VARCHAR(15) NOT NULL UNIQUE,
    CONSTRAINT uq_bloque_inicio UNIQUE (hora_inicio),
    CONSTRAINT ck_bloque_una_hora CHECK (
        TIME_TO_SEC(hora_fin) - TIME_TO_SEC(hora_inicio) = 3600
        AND TIME_TO_SEC(hora_inicio) % 3600 = 0
    )
) ENGINE=InnoDB;

-- 4. DEPARTAMENTOS (recibe datos desde "Inserccion departamentos" en semilladml)
CREATE TABLE departamentos (
    id_departamento INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- 5. CARRERAS (recibe datos desde "Inserccion carreras" en semilladml)
CREATE TABLE carreras (
    id_carrera INT AUTO_INCREMENT PRIMARY KEY,
    clave_oficial VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(120) NOT NULL,
    activa TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB;

-- 6. CATALOGO DE MATERIAS (recibe datos desde "Inserccion materias" en semilladml)
CREATE TABLE materias (
    id_materia INT AUTO_INCREMENT PRIMARY KEY,
    clave_oficial VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(120) NOT NULL,
    id_departamento INT NOT NULL,
    semestre_sugerido TINYINT NOT NULL,
    CONSTRAINT fk_mat_depto FOREIGN KEY (id_departamento) REFERENCES departamentos(id_departamento),
    CONSTRAINT ck_mat_semestre CHECK (semestre_sugerido BETWEEN 1 AND 12)
) ENGINE=InnoDB;

-- 7. RELACION CARRERA - MATERIA (N:M) (recibe datos desde "Inserccion carrera_metaria" en semilladml)
CREATE TABLE carrera_materia (
    id_carrera INT NOT NULL,
    id_materia INT NOT NULL,
    PRIMARY KEY (id_carrera, id_materia),
    CONSTRAINT fk_cm_carrera FOREIGN KEY (id_carrera) REFERENCES carreras(id_carrera) ON DELETE CASCADE,
    CONSTRAINT fk_cm_materia FOREIGN KEY (id_materia) REFERENCES materias(id_materia) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 8. CUENTAS DE USUARIO (recibe datos desde "Ingresar usuarios con contraseña hash" en semilladml)
CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    id_rol INT NOT NULL,
    correo_institucional VARCHAR(120) NOT NULL UNIQUE,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usr_rol FOREIGN KEY (id_rol) REFERENCES roles(id_rol)
) ENGINE=InnoDB;

-- 9. ESTUDIANTES (el semestre se calcula en la vista v_estudiantes_semestre)
-- (recibe datos desde "Insertar estudiantes" en semilladml)
CREATE TABLE estudiantes (
    id_estudiante INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL UNIQUE,
    matricula VARCHAR(20) NOT NULL UNIQUE,
    apellido_paterno VARCHAR(60) NOT NULL,
    apellido_materno VARCHAR(60) NULL,
    nombres VARCHAR(80) NOT NULL,
    id_carrera INT NOT NULL,
    id_periodo_ingreso INT NOT NULL,
    tipo_ingreso ENUM('Regular', 'Cambio de carrera', 'Traslado') NOT NULL DEFAULT 'Regular',
    estado ENUM('Inscrito', 'Baja temporal', 'Baja total') NOT NULL DEFAULT 'Inscrito',
    CONSTRAINT fk_est_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_est_carrera FOREIGN KEY (id_carrera) REFERENCES carreras(id_carrera),
    CONSTRAINT fk_est_periodo FOREIGN KEY (id_periodo_ingreso) REFERENCES periodos_escolares(id_periodo)
) ENGINE=InnoDB;

-- 10. DOCENTES Y TUTORES (recibe datos desde "Insertar docentes" en semilladml)
CREATE TABLE docentes (
    id_docente INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL UNIQUE,
    clave_docente VARCHAR(20) NOT NULL UNIQUE,
    apellido_paterno VARCHAR(60) NOT NULL,
    apellido_materno VARCHAR(60) NULL,
    nombres VARCHAR(80) NOT NULL,
    grado_academico ENUM('Ing.', 'Mtro.', 'Mtra.', 'Dr.', 'Dra.') NOT NULL,
    estado_laboral ENUM('Activo', 'Investigación', 'Sabático') NOT NULL DEFAULT 'Activo',
    id_departamento INT NOT NULL,
    habilitado_tutor TINYINT(1) NOT NULL DEFAULT 0,
    CONSTRAINT fk_doc_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_doc_depto FOREIGN KEY (id_departamento) REFERENCES departamentos(id_departamento),
    CONSTRAINT ck_doc_tutor_activo CHECK (habilitado_tutor = 0 OR estado_laboral = 'Activo')
) ENGINE=InnoDB;

-- 11. PERFIL DE ASESORIAS (materias autorizadas al tutor por Coordinacion)
-- (recibe datos desde "Insertar tutor_materias" en semilladml)
CREATE TABLE tutor_materias (
    id_docente INT NOT NULL,
    id_materia INT NOT NULL,
    PRIMARY KEY (id_docente, id_materia),
    CONSTRAINT fk_tm_docente FOREIGN KEY (id_docente) REFERENCES docentes(id_docente) ON DELETE CASCADE,
    CONSTRAINT fk_tm_materia FOREIGN KEY (id_materia) REFERENCES materias(id_materia) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 12A. HORARIO BASE DE ESTUDIANTE (recibe datos desde "Insertar horario_estudiante" en semilladml)
-- segunda carga recibe datos desde "Continuacion de la carga para la tabla horario_estudiante" en semilladml)
CREATE TABLE horario_estudiante (
    id_horario_est INT AUTO_INCREMENT PRIMARY KEY,
    id_estudiante INT NOT NULL,
    id_materia INT NOT NULL,
    dia_semana ENUM('Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes') NOT NULL,
    id_bloque INT NOT NULL,
    CONSTRAINT fk_he_est FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_estudiante) ON DELETE CASCADE,
    CONSTRAINT fk_he_mat FOREIGN KEY (id_materia) REFERENCES materias(id_materia),
    CONSTRAINT fk_he_blq FOREIGN KEY (id_bloque) REFERENCES bloques_horarios(id_bloque),
    CONSTRAINT uq_est_dia_blq UNIQUE (id_estudiante, dia_semana, id_bloque)
) ENGINE=InnoDB;

-- 12B. HORARIO BASE DE DOCENTE (recibe datos desde "Inserccion datos horario_docente" en semilladml)
CREATE TABLE horario_docente (
    id_horario_doc INT AUTO_INCREMENT PRIMARY KEY,
    id_docente INT NOT NULL,
    id_carrera INT NOT NULL,
    id_materia INT NOT NULL,
    dia_semana ENUM('Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes') NOT NULL,
    id_bloque INT NOT NULL,
    CONSTRAINT fk_hd_doc FOREIGN KEY (id_docente) REFERENCES docentes(id_docente) ON DELETE CASCADE,
    CONSTRAINT fk_hd_car_mat FOREIGN KEY (id_carrera, id_materia) REFERENCES carrera_materia(id_carrera, id_materia),
    CONSTRAINT fk_hd_blq FOREIGN KEY (id_bloque) REFERENCES bloques_horarios(id_bloque),
    CONSTRAINT uq_doc_dia_blq UNIQUE (id_docente, dia_semana, id_bloque)
) ENGINE=InnoDB;

-- 13. FRANJAS DE ASESORIA PUBLICADAS (recibe datos desde "Inserccion Franjas_asesorias, correccion de agotado" en semilladml)
CREATE TABLE franjas_asesoria (
    id_franja INT AUTO_INCREMENT PRIMARY KEY,
    id_docente INT NOT NULL,
    id_carrera INT NOT NULL,
    id_materia INT NOT NULL,
    fecha DATE NOT NULL,
    id_bloque INT NOT NULL,
    cupo_maximo TINYINT NOT NULL DEFAULT 10,
    estado ENUM('Publicada', 'Cancelada') NOT NULL DEFAULT 'Publicada',
    CONSTRAINT fk_fa_tutor_mat FOREIGN KEY (id_docente, id_materia) REFERENCES tutor_materias(id_docente, id_materia),
    CONSTRAINT fk_fa_car_mat FOREIGN KEY (id_carrera, id_materia) REFERENCES carrera_materia(id_carrera, id_materia),
    CONSTRAINT fk_fa_blq FOREIGN KEY (id_bloque) REFERENCES bloques_horarios(id_bloque),
    CONSTRAINT uq_doc_fecha_blq UNIQUE (id_docente, fecha, id_bloque),
    CONSTRAINT ck_fa_cupo CHECK (cupo_maximo = 10),  -- RN-04: cupo fijo de 10 lugares
    INDEX idx_fa_materia_fecha (id_materia, fecha)
) ENGINE=InnoDB;

-- 14. RESERVAS DE ASESORIA (recibe datos desde "Inserccion reserva_asesoria" en semilladml)
CREATE TABLE reservas_asesoria (
    id_reserva INT AUTO_INCREMENT PRIMARY KEY,
    id_franja INT NOT NULL,
    id_estudiante INT NOT NULL,
    tipo_cita ENUM('Inicial', 'Seguimiento') NOT NULL DEFAULT 'Inicial',
    id_reserva_origen INT NULL,
    estado_cita ENUM('Programada', 'Realizada', 'No asistio', 'Cancelada') NOT NULL DEFAULT 'Programada',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ra_franja FOREIGN KEY (id_franja) REFERENCES franjas_asesoria(id_franja),
    CONSTRAINT fk_ra_est FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_estudiante),
    CONSTRAINT uq_reserva_est UNIQUE (id_reserva, id_estudiante),
    CONSTRAINT fk_ra_origen FOREIGN KEY (id_reserva_origen, id_estudiante) REFERENCES reservas_asesoria(id_reserva, id_estudiante),
    CONSTRAINT uq_franja_est UNIQUE (id_franja, id_estudiante),
    CONSTRAINT uq_ra_origen UNIQUE (id_reserva_origen),
    CONSTRAINT ck_ra_tipo_origen CHECK (
        (tipo_cita = 'Inicial' AND id_reserva_origen IS NULL)
        OR (tipo_cita = 'Seguimiento' AND id_reserva_origen IS NOT NULL)
    )
) ENGINE=InnoDB;
-- 
-- 15. ACUERDOS TUTORIALES
CREATE TABLE acuerdos (
    id_acuerdo INT AUTO_INCREMENT PRIMARY KEY,
    id_reserva INT NOT NULL UNIQUE,
    descripcion_acuerdo TEXT NOT NULL,
    estado_acuerdo ENUM('Cerrado', 'En seguimiento') NOT NULL DEFAULT 'Cerrado',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ac_reserva FOREIGN KEY (id_reserva) REFERENCES reservas_asesoria(id_reserva) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Vistas
-- Semestre calculado como semestre calendario desde el periodo de ingreso
-- (no considera bajas temporales ni traslados que no inician en semestre 1)
CREATE VIEW v_estudiantes_semestre AS
SELECT
    e.id_estudiante,
    e.matricula,
    e.apellido_paterno,
    e.apellido_materno,
    e.nombres,
    c.nombre AS carrera,
    pi.anio AS anio_ingreso,
    pi.ciclo AS periodo_ingreso,
    ((pa.anio - pi.anio) * 2
      + (CASE WHEN pa.ciclo = 'Agosto-Diciembre' THEN 2 ELSE 1 END)
      - (CASE WHEN pi.ciclo = 'Agosto-Diciembre' THEN 2 ELSE 1 END) + 1) AS semestre_actual,
    e.tipo_ingreso,
    e.estado
FROM estudiantes e
JOIN carreras c ON e.id_carrera = c.id_carrera
JOIN periodos_escolares pi ON e.id_periodo_ingreso = pi.id_periodo
JOIN periodos_escolares pa ON pa.es_actual = 1;

-- Reservas que no están canceladas, lugares libres y estado calculado
CREATE VIEW v_franjas_cupo AS
SELECT
    f.id_franja,
    f.id_docente,
    f.id_carrera,
    f.id_materia,
    f.fecha,
    f.id_bloque,
    f.cupo_maximo,
    COUNT(r.id_reserva) AS reservas_activas,
    f.cupo_maximo - COUNT(r.id_reserva) AS lugares_libres,
    CASE
        WHEN f.estado = 'Cancelada' THEN 'Cancelada'
        WHEN COUNT(r.id_reserva) >= f.cupo_maximo THEN 'Agotada'
        ELSE 'Publicada'
    END AS estado_visible
FROM franjas_asesoria f
LEFT JOIN reservas_asesoria r
       ON r.id_franja = f.id_franja AND r.estado_cita <> 'Cancelada'
GROUP BY f.id_franja, f.id_docente, f.id_carrera, f.id_materia, f.fecha, f.id_bloque, f.cupo_maximo, f.estado;

-- TRIGGERS DE VALIDACoN (cupo, traslapes de horario y citas de seguimiento)
DELIMITER $$

-- Publicar franja: lunes a viernes, tutor habilitado y activo, sin chocar con sus clases
CREATE TRIGGER trg_franjas_bi BEFORE INSERT ON franjas_asesoria
FOR EACH ROW
BEGIN
    DECLARE v_hab TINYINT;
    DECLARE v_estado VARCHAR(20);
    DECLARE v_choque INT;

    IF WEEKDAY(NEW.fecha) > 4 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Las franjas solo pueden publicarse de lunes a viernes';
    END IF;

    SELECT habilitado_tutor, estado_laboral INTO v_hab, v_estado
      FROM docentes WHERE id_docente = NEW.id_docente;
    IF v_hab IS NULL OR v_hab = 0 OR v_estado <> 'Activo' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El docente no es un tutor habilitado y activo';
    END IF;

    SELECT COUNT(*) INTO v_choque
      FROM horario_docente
     WHERE id_docente = NEW.id_docente
       AND dia_semana + 0 = WEEKDAY(NEW.fecha) + 1
       AND id_bloque = NEW.id_bloque;
    IF v_choque > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El bloque choca con una clase del tutor';
    END IF;
END$$

-- Valida disponibilidad de la franja, carga del estudiante, cupo maximo y traslapes
-- Bloquea la franja durante la insercion para evitar sobrecupo en reservas simultaneas
CREATE TRIGGER trg_reservas_bi BEFORE INSERT ON reservas_asesoria
FOR EACH ROW
BEGIN
    DECLARE v_cupo TINYINT;
    DECLARE v_estado_franja VARCHAR(20);
    DECLARE v_fecha DATE;
    DECLARE v_bloque INT;
    DECLARE v_hora TIME;
    DECLARE v_car_franja INT;
    DECLARE v_materia INT;
    DECLARE v_docente INT;
    DECLARE v_hab TINYINT;
    DECLARE v_estado_doc VARCHAR(20);
    DECLARE v_estado_est VARCHAR(20);
    DECLARE v_car_est INT;
    DECLARE v_ocupados INT;
    DECLARE v_choque INT;
    DECLARE v_o_estado VARCHAR(20);
    DECLARE v_o_docente INT;
    DECLARE v_o_fecha DATE;
    DECLARE v_o_hora TIME;
    DECLARE v_acuerdos INT;

    SELECT f.cupo_maximo, f.estado, f.fecha, f.id_bloque, b.hora_inicio, f.id_carrera, f.id_materia, f.id_docente
      INTO v_cupo, v_estado_franja, v_fecha, v_bloque, v_hora, v_car_franja, v_materia, v_docente
      FROM franjas_asesoria f
      JOIN bloques_horarios b ON b.id_bloque = f.id_bloque
     WHERE f.id_franja = NEW.id_franja
       FOR UPDATE;

    IF v_estado_franja = 'Cancelada' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La franja está cancelada';
    END IF;

    SELECT habilitado_tutor, estado_laboral INTO v_hab, v_estado_doc
      FROM docentes WHERE id_docente = v_docente;
    IF v_hab = 0 OR v_estado_doc <> 'Activo' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El tutor ya no está habilitado';
    END IF;

    SELECT estado, id_carrera INTO v_estado_est, v_car_est
      FROM estudiantes WHERE id_estudiante = NEW.id_estudiante;
    IF v_estado_est <> 'Inscrito' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo un estudiante inscrito puede reservar';
    END IF;
    IF v_car_est <> v_car_franja THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La franja no es de la carrera del estudiante';
    END IF;

    SELECT COUNT(*) INTO v_choque
      FROM horario_estudiante
     WHERE id_estudiante = NEW.id_estudiante AND id_materia = v_materia;
    IF v_choque = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La materia no esta en la carga vigente del estudiante';
    END IF;

    SELECT COUNT(*) INTO v_ocupados
      FROM reservas_asesoria
     WHERE id_franja = NEW.id_franja AND estado_cita <> 'Cancelada'
       LOCK IN SHARE MODE;
    IF v_ocupados >= v_cupo THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La franja ya no tiene cupo';
    END IF;

    SELECT COUNT(*) INTO v_choque
      FROM horario_estudiante
     WHERE id_estudiante = NEW.id_estudiante
       AND dia_semana + 0 = WEEKDAY(v_fecha) + 1
       AND id_bloque = v_bloque;
    IF v_choque > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La franja choca con una clase del estudiante';
    END IF;

    SELECT COUNT(*) INTO v_choque
      FROM reservas_asesoria r
      JOIN franjas_asesoria f ON f.id_franja = r.id_franja
     WHERE r.id_estudiante = NEW.id_estudiante
       AND r.estado_cita <> 'Cancelada'
       AND f.fecha = v_fecha
       AND f.id_bloque = v_bloque;
    IF v_choque > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El estudiante ya tiene otra asesoria en ese horario';
    END IF;

    IF NEW.tipo_cita = 'Seguimiento' THEN
        SELECT r.estado_cita, f.id_docente, f.fecha, b.hora_inicio
          INTO v_o_estado, v_o_docente, v_o_fecha, v_o_hora
          FROM reservas_asesoria r
          JOIN franjas_asesoria f ON f.id_franja = r.id_franja
          JOIN bloques_horarios b ON b.id_bloque = f.id_bloque
         WHERE r.id_reserva = NEW.id_reserva_origen;

        IF v_o_docente <> v_docente THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El seguimiento debe ser con el mismo tutor';
        END IF;
        IF v_fecha < v_o_fecha OR (v_fecha = v_o_fecha AND v_hora <= v_o_hora) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La franja de seguimiento debe ser posterior a la cita de origen';
        END IF;
        IF v_o_estado <> 'Realizada' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La cita de origen debe estar Realizada';
        END IF;
        SELECT COUNT(*) INTO v_acuerdos
          FROM acuerdos
         WHERE id_reserva = NEW.id_reserva_origen AND estado_acuerdo = 'En seguimiento';
        IF v_acuerdos = 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La cita de origen no tiene un acuerdo En seguimiento';
        END IF;
    END IF;
END$$

-- Un acuerdo solo se registra sobre una cita Realizada
CREATE TRIGGER trg_acuerdos_bi BEFORE INSERT ON acuerdos
FOR EACH ROW
BEGIN
    DECLARE v_estado VARCHAR(20);
    SELECT estado_cita INTO v_estado FROM reservas_asesoria WHERE id_reserva = NEW.id_reserva;
    IF v_estado <> 'Realizada' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El acuerdo solo se registra sobre una cita Realizada';
    END IF;
END$$

-- La cuenta del docente solo está activa mientras esté habilitado como tutor
CREATE TRIGGER trg_docentes_ai AFTER INSERT ON docentes
FOR EACH ROW
BEGIN
    UPDATE usuarios SET activo = NEW.habilitado_tutor WHERE id_usuario = NEW.id_usuario;
END$$

CREATE TRIGGER trg_docentes_au AFTER UPDATE ON docentes
FOR EACH ROW
BEGIN
    IF NEW.habilitado_tutor <> OLD.habilitado_tutor THEN
        UPDATE usuarios SET activo = NEW.habilitado_tutor WHERE id_usuario = NEW.id_usuario;
    END IF;
END$$

DELIMITER ;

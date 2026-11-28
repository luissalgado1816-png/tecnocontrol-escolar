-- Seleccionar la base que utiliza Flask antes de ejecutar.
-- Las reservas anteriores conservan la materia de su franja.
SET NAMES utf8mb4;

ALTER TABLE reservas_asesoria ADD COLUMN IF NOT EXISTS id_materia_asesorada INT NULL;
ALTER TABLE reservas_asesoria ADD CONSTRAINT fk_ra_asesorada FOREIGN KEY IF NOT EXISTS fk_ra_asesorada (id_materia_asesorada) REFERENCES materias(id_materia);

CREATE OR REPLACE VIEW v_materias_asesorables_franja AS
 SELECT f.id_franja, m.id_materia
 FROM franjas_asesoria f
 JOIN v_materias_elegibles_tutor e ON e.id_docente=f.id_docente
     AND e.id_carrera=f.id_carrera AND e.id_materia=f.id_materia
 JOIN docentes d ON d.id_docente=f.id_docente AND d.habilitado_tutor=1
 JOIN tutor_materias tm ON tm.id_docente=f.id_docente
     AND tm.id_materia=f.id_materia AND tm.autorizada=1
 JOIN materias base ON base.id_materia=f.id_materia
 JOIN carrera_materia cm ON cm.id_carrera=f.id_carrera
 JOIN materias m ON m.id_materia=cm.id_materia
 WHERE m.id_materia=base.id_materia
    OR (m.id_departamento=base.id_departamento AND m.posicion>0 AND m.posicion<base.posicion);

DELIMITER $$
CREATE OR REPLACE TRIGGER trg_reservas_bi BEFORE INSERT ON reservas_asesoria
FOR EACH ROW
BEGIN
    DECLARE v_cupo INT;
    DECLARE v_estado_franja VARCHAR(20);
    DECLARE v_fecha DATE;
    DECLARE v_bloque INT;
    DECLARE v_hora TIME;
    DECLARE v_car_franja INT;
    DECLARE v_materia INT;
    DECLARE v_asesorada INT;
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

    IF NEW.id_materia_inscrita IS NULL THEN SET NEW.id_materia_inscrita=v_materia; END IF;
    SET v_asesorada=COALESCE(NEW.id_materia_asesorada,v_materia);
    SELECT COUNT(*) INTO v_choque
      FROM v_horario_docente_actual h
      JOIN docentes d ON d.id_docente=h.id_docente
      JOIN materias carga ON carga.id_materia=h.id_materia
      JOIN materias base ON base.id_materia=v_materia AND base.id_departamento=d.id_departamento
      JOIN tutor_materias tm ON tm.id_docente=h.id_docente
          AND tm.id_materia=base.id_materia AND tm.autorizada=1
      JOIN carrera_materia cm ON cm.id_carrera=h.id_carrera AND cm.id_materia=v_asesorada
      JOIN materias asesorada ON asesorada.id_materia=cm.id_materia
     WHERE h.id_docente=v_docente AND h.id_carrera=v_car_franja
       AND base.posicion <= CASE WHEN d.grado_academico IN ('Dr.','Dra.') THEN 3
                                 WHEN d.grado_academico IN ('Mtro.','Mtra.') THEN 2 ELSE 1 END
       AND (carga.id_materia=base.id_materia OR
           (carga.id_departamento=base.id_departamento AND base.posicion>0 AND base.posicion<carga.posicion))
       AND (asesorada.id_materia=base.id_materia OR
           (asesorada.id_departamento=base.id_departamento AND asesorada.posicion>0 AND asesorada.posicion<base.posicion));
    IF v_choque=0
       OR EXISTS (SELECT 1 FROM bloqueos_asesoria WHERE id_docente=v_docente AND v_fecha BETWEEN desde AND hasta) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='El tutor suspendió la asesoría o dejó de tener la materia autorizada';
    END IF;
    IF EXISTS (SELECT 1 FROM reservas_asesoria r JOIN franjas_asesoria f USING(id_franja)
                WHERE r.id_estudiante=NEW.id_estudiante AND r.estado_cita='Programada'
                  AND COALESCE(r.id_materia_asesorada,f.id_materia)=v_asesorada) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Ya tienes una asesoría abierta de esta materia';
    END IF;
    SELECT COUNT(*) INTO v_choque FROM v_horario_estudiante_actual h
      JOIN v_estudiantes_semestre est ON est.id_estudiante=h.id_estudiante
      JOIN carrera_materia cm ON cm.id_carrera=v_car_est AND cm.id_materia=h.id_materia AND cm.semestre=est.semestre_actual
      JOIN carrera_materia destino ON destino.id_carrera=v_car_est AND destino.id_materia=v_asesorada
      JOIN materias inscrita ON inscrita.id_materia=h.id_materia
      JOIN materias asesoria ON asesoria.id_materia=destino.id_materia
     WHERE h.id_estudiante=NEW.id_estudiante AND h.id_materia=NEW.id_materia_inscrita
       AND (inscrita.id_materia=asesoria.id_materia OR
           (inscrita.id_departamento=asesoria.id_departamento AND asesoria.posicion>0 AND asesoria.posicion<inscrita.posicion));
    IF v_choque=0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La materia no esta en la carga vigente del estudiante';
    END IF;

    SELECT COUNT(*) INTO v_ocupados
      FROM reservas_asesoria
     WHERE id_franja = NEW.id_franja AND estado_cita <> 'Cancelada';
    IF v_ocupados >= v_cupo THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La franja ya no tiene cupo';
    END IF;

    SELECT COUNT(*) INTO v_choque
      FROM v_horario_estudiante_actual
     WHERE id_estudiante = NEW.id_estudiante
       AND dia_semana + 0 = WEEKDAY(v_fecha) + 1
       AND id_bloque = v_bloque;
    IF v_choque > 0 AND (NEW.cruce_aceptado<>1 OR NEW.tipo_cita<>'Inicial') THEN
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
        IF NOT EXISTS (SELECT 1 FROM reservas_asesoria origen JOIN franjas_asesoria f USING(id_franja)
             WHERE origen.id_reserva=NEW.id_reserva_origen AND origen.id_estudiante=NEW.id_estudiante
               AND COALESCE(origen.id_materia_asesorada,f.id_materia)=v_asesorada
               AND origen.id_materia_inscrita=NEW.id_materia_inscrita) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='El seguimiento debe pertenecer a la misma atención y materia';
        END IF;
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

CREATE OR REPLACE TRIGGER trg_reservas_bu BEFORE UPDATE ON reservas_asesoria FOR EACH ROW
BEGIN
    IF NOT (NEW.id_materia_asesorada <=> OLD.id_materia_asesorada) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='La materia asesorada de una cita registrada es de solo lectura';
    END IF;
    IF OLD.estado_cita<>'Programada' AND (
       NEW.confirmada<>OLD.confirmada
       OR NEW.id_franja<>OLD.id_franja OR NEW.id_estudiante<>OLD.id_estudiante OR NEW.tipo_cita<>OLD.tipo_cita
       OR NOT (NEW.id_reserva_origen <=> OLD.id_reserva_origen) OR NOT (NEW.id_materia_inscrita <=> OLD.id_materia_inscrita)
       OR NOT (NEW.resultado_atencion <=> OLD.resultado_atencion) OR NOT (NEW.anotaciones <=> OLD.anotaciones)
       OR NEW.cruce_aceptado<>OLD.cruce_aceptado
       OR (
           (NEW.estado_cita<>OLD.estado_cita OR NOT (NEW.motivo_cancelacion <=> OLD.motivo_cancelacion))
           AND NOT (
               OLD.estado_cita='Cancelada' AND (OLD.motivo_cancelacion <=> 'Suspensión del docente')
               AND (
                   (NEW.estado_cita='Cancelada' AND (NEW.motivo_cancelacion <=> 'Suspensión del docente · no restablecida'))
                   OR (
                       NEW.estado_cita='Programada' AND NEW.motivo_cancelacion IS NULL
                       AND EXISTS (
                           SELECT 1 FROM franjas_asesoria f
                           JOIN bloques_horarios b USING(id_bloque)
                           WHERE f.id_franja=OLD.id_franja AND f.estado='Publicada'
                             AND (f.fecha>CURRENT_DATE() OR (f.fecha=CURRENT_DATE() AND b.hora_inicio>CURRENT_TIME()))
                             AND NOT EXISTS (
                                 SELECT 1 FROM bloqueos_asesoria x
                                 WHERE x.id_docente=f.id_docente AND f.fecha BETWEEN x.desde AND x.hasta
                             )
                       )
                   )
               )
           )
       )) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='La atención guardada es de solo lectura';
    END IF;
END$$
DELIMITER ;

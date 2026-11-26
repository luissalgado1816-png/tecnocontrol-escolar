-- Aplicar en la base que se usa para las pruebas.
SET NAMES utf8mb4;

DELIMITER $$
CREATE OR REPLACE TRIGGER trg_reservas_bu BEFORE UPDATE ON reservas_asesoria FOR EACH ROW
BEGIN
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

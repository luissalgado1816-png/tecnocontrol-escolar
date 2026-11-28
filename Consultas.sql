-- Active: 1794701908966@@127.0.0.1@3306@mysql
USE tecnocontrol_escolar;
select * from estudiantes;
select * from docentes;

select * from v_materias_elegibles_tutor;

USE tecnocontrol_escolar;
--Consulta para obtener los docentes y las materias que pueden tutorizar
SELECT d.id_docente, d.clave_docente, d.nombres, d.habilitado_tutor, m.clave_oficial, m.nombre AS materia, tm.autorizada
FROM docentes d
JOIN tutor_materias tm ON tm.id_docente = d.id_docente
JOIN materias m ON m.id_materia = tm.id_materia
WHERE d.clave_docente = 'DOC01';

--Consulta para obtener materias asesoradas
SELECT f.id_franja, f.fecha, b.etiqueta AS horario, m.nombre AS materia, f.cupo_maximo, f.estado,
       r.id_reserva, e.matricula, r.estado_cita
FROM franjas_asesoria f
JOIN bloques_horarios b ON b.id_bloque = f.id_bloque
JOIN materias m ON m.id_materia = f.id_materia
LEFT JOIN reservas_asesoria r ON r.id_franja = f.id_franja
LEFT JOIN estudiantes e ON e.id_estudiante = r.id_estudiante
ORDER BY f.id_franja DESC LIMIT 5;

--Persistencia verificada en MariaDB
USE tecnocontrol_escolar;

SELECT f.id_franja, f.fecha, f.cupo_maximo, f.reservas_activas, f.lugares_libres, f.estado_visible,
       r.id_reserva, r.estado_cita, r.motivo_cancelacion
FROM v_franjas_cupo f
LEFT JOIN reservas_asesoria r ON r.id_franja = f.id_franja
ORDER BY f.id_franja DESC
LIMIT 5;

USE tecnocontrol_escolar;

SELECT e.matricula, CONCAT(e.nombres, ' ', e.apellido_paterno) AS estudiante,
       d.clave_docente, CONCAT(d.nombres, ' ', d.apellido_paterno) AS tutor,
       f.fecha, b.etiqueta AS horario, m.nombre AS materia,
       r.estado_cita, a.descripcion_acuerdo, a.estado_acuerdo
FROM reservas_asesoria r
JOIN estudiantes e ON e.id_estudiante = r.id_estudiante
JOIN franjas_asesoria f ON f.id_franja = r.id_franja
JOIN docentes d ON d.id_docente = f.id_docente
JOIN bloques_horarios b ON b.id_bloque = f.id_bloque
JOIN materias m ON m.id_materia = COALESCE(r.id_materia_asesorada, f.id_materia)
LEFT JOIN acuerdos a ON a.id_reserva = r.id_reserva
WHERE e.matricula = '26090201';





//cargar la base inicial
//findstr /M /C:"v_materias_asesorables_franja" database.sql && type semilladml.sql >nul && "%TC_MYSQL%" %TC_OPTS% -e "DROP DATABASE tecnocontrol_escolar" && "%TC_MYSQL%" %TC_OPTS% < database.sql && "%TC_MYSQL%" %TC_OPTS% < semilladml.sql >nul && echo Base inicial cargada
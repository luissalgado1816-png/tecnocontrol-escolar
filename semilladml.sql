-- Active: 1794701908966@@127.0.0.1@3306@mysql
-- TecnoControl Escolar. Ejecutar después de database.sql.
USE tecnocontrol_escolar;
SET NAMES utf8mb4;
START TRANSACTION;
SET @demo = NOT EXISTS (SELECT 1 FROM usuarios);
-- Catálogos comunes. Las cuentas y operaciones de ejemplo solo se cargan en la primera instalación.

INSERT INTO roles (codigo_rol,nombre_actor) VALUES
('admin_escolar', 'Administrador Escolar'),
('coordinador_tutorias', 'Coordinador de Tutorías'),
('consulta_seguimiento', 'Tutor'),
('consulta_seguimiento_est', 'Estudiante')
ON DUPLICATE KEY UPDATE codigo_rol=VALUES(codigo_rol);

SET @sin_periodo = NOT EXISTS (SELECT 1 FROM periodos_escolares WHERE es_actual=1);
INSERT INTO periodos_escolares(anio,ciclo,es_actual) VALUES (2025,'Agosto-Diciembre',0),(2026,'Enero-Junio',0),(2026,'Agosto-Diciembre',0)
ON DUPLICATE KEY UPDATE anio=VALUES(anio);
UPDATE periodos_escolares SET es_actual=1 WHERE anio=2026 AND ciclo='Agosto-Diciembre' AND @sin_periodo=1;

INSERT INTO bloques_horarios(hora_inicio,hora_fin,etiqueta) VALUES
('07:00', '08:00', '07:00-08:00'),
('08:00', '09:00', '08:00-09:00'),
('09:00', '10:00', '09:00-10:00'),
('10:00', '11:00', '10:00-11:00'),
('11:00', '12:00', '11:00-12:00'),
('12:00', '13:00', '12:00-13:00'),
('13:00', '14:00', '13:00-14:00'),
('14:00', '15:00', '14:00-15:00'),
('15:00', '16:00', '15:00-16:00'),
('16:00', '17:00', '16:00-17:00'),
('17:00', '18:00', '17:00-18:00'),
('18:00', '19:00', '18:00-19:00'),
('19:00', '20:00', '19:00-20:00')
ON DUPLICATE KEY UPDATE hora_inicio=VALUES(hora_inicio);

INSERT INTO departamentos(nombre) VALUES
('Ciencias Básicas'),
('Sistemas y Computación'),
('Metalmecánica')
ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);

INSERT INTO carreras(clave_oficial,nombre) VALUES
('ISIC-2010-224', 'Ingeniería en Sistemas Computacionales'),
('IEME-2010-210', 'Ingeniería Electromecánica')
ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);

-- Conservar los identificadores y los horarios al corregir dos claves de la primera versión.
UPDATE materias m LEFT JOIN materias oficial ON oficial.clave_oficial='SCD-1011'
SET m.clave_oficial='SCD-1011' WHERE m.clave_oficial='SCD-1008' AND m.nombre='Ingeniería de Software' AND oficial.id_materia IS NULL;
UPDATE materias m LEFT JOIN materias oficial ON oficial.clave_oficial='SCA-1026'
SET m.clave_oficial='SCA-1026' WHERE m.clave_oficial='SCA1034' AND m.nombre='Taller de Sistemas Operativos' AND oficial.id_materia IS NULL;
-- Planes ISIC-2010-224 e IEME-2010-210. Clave, asignatura y semestre provienen de las retículas.
CREATE TEMPORARY TABLE tmp_reticula (plan VARCHAR(20),semestre TINYINT,clave VARCHAR(20),nombre VARCHAR(120),departamento VARCHAR(100),posicion TINYINT,PRIMARY KEY(plan,clave));

INSERT INTO tmp_reticula VALUES
('ISIC-2010-224', 1, 'ACA-0907', 'Taller de ética', 'Ciencias Básicas', 0),
('ISIC-2010-224', 1, 'ACC-0906', 'Fundamentos de investigación', 'Ciencias Básicas', 0),
('ISIC-2010-224', 1, 'ACF-0901', 'Cálculo diferencial', 'Ciencias Básicas', 1),
('ISIC-2010-224', 1, 'AED-1285', 'Fundamentos de programación', 'Sistemas y Computación', 1),
('ISIC-2010-224', 1, 'AEF-1041', 'Matemáticas discretas', 'Sistemas y Computación', 0),
('ISIC-2010-224', 1, 'SCH-1024', 'Taller de administración', 'Sistemas y Computación', 0),
('ISIC-2010-224', 2, 'ACF-0902', 'Cálculo integral', 'Ciencias Básicas', 2),
('ISIC-2010-224', 2, 'ACF-0903', 'Álgebra lineal', 'Ciencias Básicas', 0),
('ISIC-2010-224', 2, 'AEC-1008', 'Contabilidad financiera', 'Sistemas y Computación', 0),
('ISIC-2010-224', 2, 'AEC-1058', 'Química', 'Ciencias Básicas', 0),
('ISIC-2010-224', 2, 'AED-1286', 'Programación orientada a objetos', 'Sistemas y Computación', 2),
('ISIC-2010-224', 2, 'AEF-1052', 'Probabilidad y estadística', 'Ciencias Básicas', 0),
('ISIC-2010-224', 3, 'ACD-0908', 'Desarrollo sustentable', 'Ciencias Básicas', 0),
('ISIC-2010-224', 3, 'ACF-0904', 'Cálculo vectorial', 'Ciencias Básicas', 3),
('ISIC-2010-224', 3, 'AED-1026', 'Estructura de datos', 'Sistemas y Computación', 3),
('ISIC-2010-224', 3, 'SCC-1005', 'Cultura empresarial', 'Sistemas y Computación', 0),
('ISIC-2010-224', 3, 'SCC-1013', 'Investigación de operaciones', 'Sistemas y Computación', 0),
('ISIC-2010-224', 3, 'SCF-1006', 'Física general', 'Ciencias Básicas', 0),
('ISIC-2010-224', 4, 'ACF-0905', 'Ecuaciones diferenciales', 'Ciencias Básicas', 0),
('ISIC-2010-224', 4, 'AEF-1031', 'Fundamentos de base de datos', 'Sistemas y Computación', 0),
('ISIC-2010-224', 4, 'SCC-1017', 'Métodos numéricos', 'Sistemas y Computación', 0),
('ISIC-2010-224', 4, 'SCD-1018', 'Principios eléctricos y aplicaciones digitales', 'Sistemas y Computación', 0),
('ISIC-2010-224', 4, 'SCD-1022', 'Simulación', 'Sistemas y Computación', 0),
('ISIC-2010-224', 4, 'SCD-1027', 'Tópicos avanzados de programación', 'Sistemas y Computación', 0),
('ISIC-2010-224', 5, 'AEC-1034', 'Fundamentos de telecomunicaciones', 'Sistemas y Computación', 0),
('ISIC-2010-224', 5, 'AEC-1061', 'Sistemas operativos', 'Sistemas y Computación', 0),
('ISIC-2010-224', 5, 'SCA-1025', 'Taller de base de datos', 'Sistemas y Computación', 0),
('ISIC-2010-224', 5, 'SCC-1007', 'Fundamentos de ingeniería de software', 'Sistemas y Computación', 0),
('ISIC-2010-224', 5, 'SCC-1010', 'Graficación', 'Sistemas y Computación', 0),
('ISIC-2010-224', 5, 'SCD-1003', 'Arquitectura de computadoras', 'Sistemas y Computación', 0),
('ISIC-2010-224', 6, 'SCA-1026', 'Taller de sistemas operativos', 'Sistemas y Computación', 0),
('ISIC-2010-224', 6, 'SCB-1001', 'Administración de base de datos', 'Sistemas y Computación', 0),
('ISIC-2010-224', 6, 'SCC-1014', 'Lenguajes de interfaz', 'Sistemas y Computación', 0),
('ISIC-2010-224', 6, 'SCD-1011', 'Ingeniería de software', 'Sistemas y Computación', 0),
('ISIC-2010-224', 6, 'SCD-1015', 'Lenguajes y autómatas I', 'Sistemas y Computación', 0),
('ISIC-2010-224', 6, 'SCD-1021', 'Redes de computadoras', 'Sistemas y Computación', 0),
('ISIC-2010-224', 7, 'ACA-0909', 'Taller de investigación I', 'Ciencias Básicas', 0),
('ISIC-2010-224', 7, 'SCC-1023', 'Sistemas programables', 'Sistemas y Computación', 0),
('ISIC-2010-224', 7, 'SCD-1004', 'Conmutación y enrutamiento en redes de datos', 'Sistemas y Computación', 0),
('ISIC-2010-224', 7, 'SCD-1016', 'Lenguajes y autómatas II', 'Sistemas y Computación', 0),
('ISIC-2010-224', 7, 'SCG-1009', 'Gestión de proyectos de software', 'Sistemas y Computación', 0),
('ISIC-2010-224', 8, 'ACA-0910', 'Taller de investigación II', 'Ciencias Básicas', 0),
('ISIC-2010-224', 8, 'AEB-1055', 'Programación web', 'Sistemas y Computación', 0),
('ISIC-2010-224', 8, 'SCA-1002', 'Administración de redes', 'Sistemas y Computación', 0),
('ISIC-2010-224', 8, 'SCC-1019', 'Programación lógica y funcional', 'Sistemas y Computación', 0),
('ISIC-2010-224', 9, 'SCC-1012', 'Inteligencia artificial', 'Sistemas y Computación', 0),
('IEME-2010-210', 1, 'ACA-0907', 'Taller de ética', 'Ciencias Básicas', 0),
('IEME-2010-210', 1, 'ACC-0906', 'Fundamentos de investigación', 'Ciencias Básicas', 0),
('IEME-2010-210', 1, 'ACD-0908', 'Desarrollo sustentable', 'Ciencias Básicas', 0),
('IEME-2010-210', 1, 'ACF-0901', 'Cálculo diferencial', 'Ciencias Básicas', 1),
('IEME-2010-210', 1, 'AEC-1058', 'Química', 'Ciencias Básicas', 0),
('IEME-2010-210', 1, 'EMH-1016', 'Introducción a la programación', 'Metalmecánica', 0),
('IEME-2010-210', 2, 'ACF-0902', 'Cálculo integral', 'Ciencias Básicas', 2),
('IEME-2010-210', 2, 'ACF-0903', 'Álgebra lineal', 'Ciencias Básicas', 0),
('IEME-2010-210', 2, 'AEC-1047', 'Metrología y normalización', 'Metalmecánica', 0),
('IEME-2010-210', 2, 'AEF-1390', 'Dibujo electromecánico', 'Metalmecánica', 0),
('IEME-2010-210', 2, 'EME-1012', 'Estática', 'Metalmecánica', 0),
('IEME-2010-210', 2, 'EME-1028', 'Tecnología de los materiales', 'Metalmecánica', 0),
('IEME-2010-210', 3, 'ACF-0904', 'Cálculo vectorial', 'Ciencias Básicas', 3),
('IEME-2010-210', 3, 'AEE-1051', 'Probabilidad y estadística', 'Ciencias Básicas', 0),
('IEME-2010-210', 3, 'EMC-1011', 'Electricidad y magnetismo', 'Metalmecánica', 0),
('IEME-2010-210', 3, 'EMC-1022', 'Procesos de manufactura', 'Metalmecánica', 0),
('IEME-2010-210', 3, 'EME-1008', 'Dinámica', 'Metalmecánica', 0),
('IEME-2010-210', 3, 'EMJ-1021', 'Mecánica de materiales', 'Metalmecánica', 0),
('IEME-2010-210', 4, 'ACF-0905', 'Ecuaciones diferenciales', 'Ciencias Básicas', 0),
('IEME-2010-210', 4, 'AEF-1021', 'Electrónica analógica', 'Metalmecánica', 0),
('IEME-2010-210', 4, 'EME-1005', 'Análisis y síntesis de mecanismos', 'Metalmecánica', 0),
('IEME-2010-210', 4, 'EME-1020', 'Mecánica de fluidos', 'Metalmecánica', 0),
('IEME-2010-210', 4, 'EME-1029', 'Termodinámica', 'Metalmecánica', 1),
('IEME-2010-210', 4, 'EMF-1004', 'Análisis de circuitos eléctricos de CD', 'Metalmecánica', 0),
('IEME-2010-210', 5, 'AEC-1022', 'Electrónica digital', 'Metalmecánica', 0),
('IEME-2010-210', 5, 'EMC-1010', 'Diseño e ingeniería asistidos por computadora', 'Metalmecánica', 0),
('IEME-2010-210', 5, 'EME-1030', 'Transferencia de calor', 'Metalmecánica', 2),
('IEME-2010-210', 5, 'EMF-1003', 'Análisis de circuitos eléctricos de CA', 'Metalmecánica', 0),
('IEME-2010-210', 5, 'EMF-1009', 'Diseño de elementos de máquinas', 'Metalmecánica', 0),
('IEME-2010-210', 5, 'EMJ-1026', 'Sistemas y máquinas de fluidos', 'Metalmecánica', 0),
('IEME-2010-210', 6, 'ACA-0909', 'Taller de investigación I', 'Ciencias Básicas', 0),
('IEME-2010-210', 6, 'EMC-1018', 'Máquinas y equipos térmicos I', 'Metalmecánica', 3),
('IEME-2010-210', 6, 'EMF-1015', 'Instalaciones eléctricas', 'Metalmecánica', 0),
('IEME-2010-210', 6, 'EMJ-1001', 'Administración y técnicas de mantenimiento', 'Metalmecánica', 0),
('IEME-2010-210', 6, 'EMJ-1002', 'Ahorro de energía', 'Metalmecánica', 0),
('IEME-2010-210', 6, 'EMJ-1017', 'Máquinas eléctricas', 'Metalmecánica', 0),
('IEME-2010-210', 7, 'ACA-0910', 'Taller de investigación II', 'Ciencias Básicas', 0),
('IEME-2010-210', 7, 'EMC-1019', 'Máquinas y equipos térmicos II', 'Metalmecánica', 0),
('IEME-2010-210', 7, 'EMF-1006', 'Controles eléctricos', 'Metalmecánica', 0),
('IEME-2010-210', 7, 'EMF-1024', 'Sistemas eléctricos de potencia', 'Metalmecánica', 0),
('IEME-2010-210', 7, 'EMJ-1014', 'Ingeniería de control clásico', 'Metalmecánica', 0),
('IEME-2010-210', 8, 'EMC-1013', 'Formulación y evaluación de proyectos', 'Metalmecánica', 0),
('IEME-2010-210', 8, 'EMF-1023', 'Refrigeración y aire acondicionado', 'Metalmecánica', 0),
('IEME-2010-210', 8, 'EMF-1027', 'Subestaciones eléctricas', 'Metalmecánica', 0),
('IEME-2010-210', 8, 'EMJ-1025', 'Sistemas hidráulicos y neumáticos de potencia', 'Metalmecánica', 0);

INSERT INTO materias(clave_oficial,nombre,id_departamento,semestre_sugerido,posicion)
SELECT t.clave,MIN(t.nombre),MIN(d.id_departamento),MIN(t.semestre),MAX(t.posicion) FROM tmp_reticula t JOIN departamentos d ON d.nombre=t.departamento GROUP BY t.clave
ON DUPLICATE KEY UPDATE nombre=VALUES(nombre),posicion=VALUES(posicion);
INSERT INTO carrera_materia (id_carrera,id_materia,semestre)
SELECT c.id_carrera,m.id_materia,t.semestre FROM tmp_reticula t JOIN carreras c ON c.clave_oficial=t.plan JOIN materias m ON m.clave_oficial=t.clave
ON DUPLICATE KEY UPDATE semestre=VALUES(semestre);
DROP TEMPORARY TABLE tmp_reticula;
-- Datos de demostración. Los horarios y los grados corresponden al escenario académico.

SET @rol0 = (SELECT id_rol FROM roles WHERE codigo_rol='admin_escolar');

SET @rol1 = (SELECT id_rol FROM roles WHERE codigo_rol='coordinador_tutorias');

SET @rol2 = (SELECT id_rol FROM roles WHERE codigo_rol='consulta_seguimiento');

SET @rol3 = (SELECT id_rol FROM roles WHERE codigo_rol='consulta_seguimiento_est');

SET @dep0 = (SELECT id_departamento FROM departamentos WHERE nombre='Ciencias Básicas');

SET @dep1 = (SELECT id_departamento FROM departamentos WHERE nombre='Sistemas y Computación');

SET @dep2 = (SELECT id_departamento FROM departamentos WHERE nombre='Metalmecánica');

SET @sis = (SELECT id_carrera FROM carreras WHERE clave_oficial='ISIC-2010-224');

SET @electro = (SELECT id_carrera FROM carreras WHERE clave_oficial='IEME-2010-210');

SET @p2025 = (SELECT id_periodo FROM periodos_escolares WHERE anio=2025 AND ciclo='Agosto-Diciembre');

SET @p2026 = (SELECT id_periodo FROM periodos_escolares WHERE anio=2026 AND ciclo='Agosto-Diciembre');

SET @h7 = (SELECT id_bloque FROM bloques_horarios WHERE hora_inicio='07:00');

SET @h8 = (SELECT id_bloque FROM bloques_horarios WHERE hora_inicio='08:00');

SET @h9 = (SELECT id_bloque FROM bloques_horarios WHERE hora_inicio='09:00');

SET @h10 = (SELECT id_bloque FROM bloques_horarios WHERE hora_inicio='10:00');

SET @h11 = (SELECT id_bloque FROM bloques_horarios WHERE hora_inicio='11:00');

SET @h12 = (SELECT id_bloque FROM bloques_horarios WHERE hora_inicio='12:00');

SET @h13 = (SELECT id_bloque FROM bloques_horarios WHERE hora_inicio='13:00');

SET @h14 = (SELECT id_bloque FROM bloques_horarios WHERE hora_inicio='14:00');

SET @h15 = (SELECT id_bloque FROM bloques_horarios WHERE hora_inicio='15:00');

SET @h16 = (SELECT id_bloque FROM bloques_horarios WHERE hora_inicio='16:00');

SET @h17 = (SELECT id_bloque FROM bloques_horarios WHERE hora_inicio='17:00');

SET @h18 = (SELECT id_bloque FROM bloques_horarios WHERE hora_inicio='18:00');

SET @h19 = (SELECT id_bloque FROM bloques_horarios WHERE hora_inicio='19:00');

SET @m_ACA_0907 = (SELECT id_materia FROM materias WHERE clave_oficial='ACA-0907');

SET @m_ACC_0906 = (SELECT id_materia FROM materias WHERE clave_oficial='ACC-0906');

SET @m_ACD_0908 = (SELECT id_materia FROM materias WHERE clave_oficial='ACD-0908');

SET @m_ACF_0901 = (SELECT id_materia FROM materias WHERE clave_oficial='ACF-0901');

SET @m_ACF_0902 = (SELECT id_materia FROM materias WHERE clave_oficial='ACF-0902');

SET @m_ACF_0904 = (SELECT id_materia FROM materias WHERE clave_oficial='ACF-0904');

SET @m_AED_1026 = (SELECT id_materia FROM materias WHERE clave_oficial='AED-1026');

SET @m_AED_1285 = (SELECT id_materia FROM materias WHERE clave_oficial='AED-1285');

SET @m_AED_1286 = (SELECT id_materia FROM materias WHERE clave_oficial='AED-1286');

SET @m_AEE_1051 = (SELECT id_materia FROM materias WHERE clave_oficial='AEE-1051');

SET @m_AEF_1041 = (SELECT id_materia FROM materias WHERE clave_oficial='AEF-1041');

SET @m_EMC_1011 = (SELECT id_materia FROM materias WHERE clave_oficial='EMC-1011');

SET @m_EMC_1018 = (SELECT id_materia FROM materias WHERE clave_oficial='EMC-1018');

SET @m_EMC_1022 = (SELECT id_materia FROM materias WHERE clave_oficial='EMC-1022');

SET @m_EME_1008 = (SELECT id_materia FROM materias WHERE clave_oficial='EME-1008');

SET @m_EME_1029 = (SELECT id_materia FROM materias WHERE clave_oficial='EME-1029');

SET @m_EME_1030 = (SELECT id_materia FROM materias WHERE clave_oficial='EME-1030');

SET @m_EMJ_1021 = (SELECT id_materia FROM materias WHERE clave_oficial='EMJ-1021');

SET @m_SCC_1005 = (SELECT id_materia FROM materias WHERE clave_oficial='SCC-1005');

SET @m_SCC_1013 = (SELECT id_materia FROM materias WHERE clave_oficial='SCC-1013');

SET @m_SCF_1006 = (SELECT id_materia FROM materias WHERE clave_oficial='SCF-1006');

SET @m_SCH_1024 = (SELECT id_materia FROM materias WHERE clave_oficial='SCH-1024');

INSERT INTO usuarios (username,password_hash,id_rol,correo_institucional,activo)
SELECT 'adminescolar0001', 'scrypt:32768:8:1$oU2CMqZYpLNbw1Rb$0512584bf76ba68139f972462d842e09357f1d96903985dcf86778cf52d16516695f9239ab70d730ff1f67675d51334fc0985592bed2222d8e1830e9f721090a', @rol0, 'admin.escolar@zacatepec.tecnm.mx', 1 WHERE @demo = 1;

SET @uadmin = (SELECT id_usuario FROM usuarios WHERE username='adminescolar0001');

INSERT INTO usuarios (username,password_hash,id_rol,correo_institucional,activo)
SELECT 'coordinadortutoria0001', 'scrypt:32768:8:1$Ru5NjbEY6ukYtueN$a2b940baaad8706d6e16e6bd3c6d219dc9facf089347dec363e0483a82ea740ffd88f9368b1666eca32c945d0a572cf6f0fa6a877cdc48b224925b1589d2d13b', @rol1, 'tutorias@zacatepec.tecnm.mx', 1 WHERE @demo = 1;

SET @ucoord = (SELECT id_usuario FROM usuarios WHERE username='coordinadortutoria0001');

INSERT INTO usuarios (username,password_hash,id_rol,correo_institucional,activo)
SELECT 'maestro0001', 'scrypt:32768:8:1$zOXMH6dJwP0x9GcL$5c167b32aa08a13531eee499b0246bd3720318f6e0ba0cece8a1f533e717f369aec4785d4fb535c7281c53723e039fc5b6fe82869818fa7daa02ff3f39c08783', @rol2, 'demo.docente01@zacatepec.tecnm.mx', 1 WHERE @demo = 1;

SET @ud1 = (SELECT id_usuario FROM usuarios WHERE username='maestro0001');

INSERT INTO docentes (id_usuario,clave_docente,apellido_paterno,apellido_materno,nombres,grado_academico,estado_laboral,id_departamento,habilitado_tutor)
SELECT @ud1, 'DOC-101', 'Sandoval', 'Jacobo', 'Ángel', 'Ing.', 'Activo', @dep0, 1 WHERE @demo = 1;

SET @d1 = (SELECT id_docente FROM docentes WHERE id_usuario=@ud1);

INSERT INTO usuarios (username,password_hash,id_rol,correo_institucional,activo)
SELECT 'maestro0002', 'scrypt:32768:8:1$Z9egQB5pFLN9huLZ$c6e39f7ebe6723e6d0adced1651503043d587fe70592bcfd5ce49075764c76fff3e906095f4f0f46ccd332b6307a3815826baca43c7cbace5ab9ff92c0e7e795', @rol2, 'demo.docente02@zacatepec.tecnm.mx', 1 WHERE @demo = 1;

SET @ud2 = (SELECT id_usuario FROM usuarios WHERE username='maestro0002');

INSERT INTO docentes (id_usuario,clave_docente,apellido_paterno,apellido_materno,nombres,grado_academico,estado_laboral,id_departamento,habilitado_tutor)
SELECT @ud2, 'DOC-102', 'Rojas', 'Vilchis', 'Ma. Guadalupe', 'Ing.', 'Activo', @dep1, 1 WHERE @demo = 1;

SET @d2 = (SELECT id_docente FROM docentes WHERE id_usuario=@ud2);

INSERT INTO usuarios (username,password_hash,id_rol,correo_institucional,activo)
SELECT 'maestro0003', 'scrypt:32768:8:1$IV4l4c8uDGknxgT7$e1259f9aa43a9ae29d604c5bd095b898246898c3e90cb2759346e43e42a5ef3ff3e54b91441a17a8b6e1d4b10e8aad8a4f394d3b704c71c180a4fb026bb31019', @rol2, 'demo.docente03@zacatepec.tecnm.mx', 1 WHERE @demo = 1;

SET @ud3 = (SELECT id_usuario FROM usuarios WHERE username='maestro0003');

INSERT INTO docentes (id_usuario,clave_docente,apellido_paterno,apellido_materno,nombres,grado_academico,estado_laboral,id_departamento,habilitado_tutor)
SELECT @ud3, 'DOC-103', 'Manzo', 'Espín', 'Jesús', 'Mtro.', 'Activo', @dep0, 1 WHERE @demo = 1;

SET @d3 = (SELECT id_docente FROM docentes WHERE id_usuario=@ud3);

INSERT INTO usuarios (username,password_hash,id_rol,correo_institucional,activo)
SELECT 'maestro0004', 'scrypt:32768:8:1$tsL6FXZeoXH2xIsB$18a3640d79ee86af46da0c843f8f0aac7e908ce80f050c8086577e3cbd7f15857651ae4e35b9208b34e05b7c781223e8de81fe554680827c6a161d52ce58012d', @rol2, 'demo.docente04@zacatepec.tecnm.mx', 1 WHERE @demo = 1;

SET @ud4 = (SELECT id_usuario FROM usuarios WHERE username='maestro0004');

INSERT INTO docentes (id_usuario,clave_docente,apellido_paterno,apellido_materno,nombres,grado_academico,estado_laboral,id_departamento,habilitado_tutor)
SELECT @ud4, 'DOC-104', 'Castañeda', 'Martínez', 'Felipe', 'Mtro.', 'Activo', @dep1, 1 WHERE @demo = 1;

SET @d4 = (SELECT id_docente FROM docentes WHERE id_usuario=@ud4);

INSERT INTO usuarios (username,password_hash,id_rol,correo_institucional,activo)
SELECT 'maestro0005', 'scrypt:32768:8:1$pxkoQtcImXVHkBad$833cd2c65f05ef59766710f0ed4184c29a532665d1a1ff544d1f44e5e9f135e498716bb3e204960d4e8016bad7194054133059c831de4fc2d35c7915acea0e9c', @rol2, 'demo.docente05@zacatepec.tecnm.mx', 1 WHERE @demo = 1;

SET @ud5 = (SELECT id_usuario FROM usuarios WHERE username='maestro0005');

INSERT INTO docentes (id_usuario,clave_docente,apellido_paterno,apellido_materno,nombres,grado_academico,estado_laboral,id_departamento,habilitado_tutor)
SELECT @ud5, 'DOC-105', 'Moreno', 'Altamirano', 'Ana Delia', 'Dr.', 'Activo', @dep0, 1 WHERE @demo = 1;

SET @d5 = (SELECT id_docente FROM docentes WHERE id_usuario=@ud5);

INSERT INTO usuarios (username,password_hash,id_rol,correo_institucional,activo)
SELECT 'maestro0006', 'scrypt:32768:8:1$hIbaN98Nzlatb8J8$66d017f131e4a1229420d1e17b019c3098bd4f8a6ca69c3d6e415990adf33aa762b7a8f12185045a1e1e1c2a7b45eb7268026d4b62c206658891ae6bd07e6080', @rol2, 'demo.docente06@zacatepec.tecnm.mx', 1 WHERE @demo = 1;

SET @ud6 = (SELECT id_usuario FROM usuarios WHERE username='maestro0006');

INSERT INTO docentes (id_usuario,clave_docente,apellido_paterno,apellido_materno,nombres,grado_academico,estado_laboral,id_departamento,habilitado_tutor)
SELECT @ud6, 'DOC-106', 'Velázquez', 'Santana', 'José Antonio', 'Dr.', 'Activo', @dep1, 1 WHERE @demo = 1;

SET @d6 = (SELECT id_docente FROM docentes WHERE id_usuario=@ud6);

INSERT INTO usuarios (username,password_hash,id_rol,correo_institucional,activo)
SELECT 'maestro0007', 'scrypt:32768:8:1$mWDrC9uVjX8wEtBz$b08448d72b19615a84cb78909730d82b256dd71ec2b2096ebae8d693977039680e699cd246006ed41a09b073f7ab5be8fa9bbba3476542ebdb35eeff83b50fc8', @rol2, 'demo.docente07@zacatepec.tecnm.mx', 1 WHERE @demo = 1;

SET @ud7 = (SELECT id_usuario FROM usuarios WHERE username='maestro0007');

INSERT INTO docentes (id_usuario,clave_docente,apellido_paterno,apellido_materno,nombres,grado_academico,estado_laboral,id_departamento,habilitado_tutor)
SELECT @ud7, 'DOC-107', 'Ríos', 'Beltrán', 'Mariana', 'Dr.', 'Activo', @dep2, 1 WHERE @demo = 1;

SET @d7 = (SELECT id_docente FROM docentes WHERE id_usuario=@ud7);

INSERT INTO usuarios (username,password_hash,id_rol,correo_institucional,activo)
SELECT 'maestro0008', 'scrypt:32768:8:1$O5RmVlm4YCNjwa2u$8917e5a898561836fc8ab0dcbbcb294fa5f41c79172e347ec01abbfd4fca4bda8060e68b78487a94029a48d80b7a9641b3d7ee8bc2bde635cdcc1cb188d9d9f8', @rol2, 'demo.docente08@zacatepec.tecnm.mx', 1 WHERE @demo = 1;

SET @ud8 = (SELECT id_usuario FROM usuarios WHERE username='maestro0008');

INSERT INTO docentes (id_usuario,clave_docente,apellido_paterno,apellido_materno,nombres,grado_academico,estado_laboral,id_departamento,habilitado_tutor)
SELECT @ud8, 'DOC-108', 'Luna', 'Serrano', 'Gabriel', 'Dr.', 'Activo', @dep2, 1 WHERE @demo = 1;

SET @d8 = (SELECT id_docente FROM docentes WHERE id_usuario=@ud8);

INSERT INTO usuarios (username,password_hash,id_rol,correo_institucional,activo)
SELECT 'maestro0009', 'scrypt:32768:8:1$W8w2qIIJ9phOM4AR$119974021c0c460b0b16cdf50b862a2a485b6d0b87650090b85d0822429c4870cdbde40f55efa87c472655982417c77dcca79330905389fa20bc8be346e2775a', @rol2, 'demo.docente09@zacatepec.tecnm.mx', 1 WHERE @demo = 1;

SET @ud9 = (SELECT id_usuario FROM usuarios WHERE username='maestro0009');

INSERT INTO docentes (id_usuario,clave_docente,apellido_paterno,apellido_materno,nombres,grado_academico,estado_laboral,id_departamento,habilitado_tutor)
SELECT @ud9, 'DOC-109', 'Ortega', 'Vidal', 'Elena', 'Dr.', 'Activo', @dep2, 1 WHERE @demo = 1;

SET @d9 = (SELECT id_docente FROM docentes WHERE id_usuario=@ud9);

INSERT INTO usuarios (username,password_hash,id_rol,correo_institucional,activo)
SELECT '26090101', 'scrypt:32768:8:1$oeg88nSy739zwRRv$4120d1e970b4ac525cca12d09221260f24f8b275f738a7f73f4082043eb74df03aab5eee17400115999a7038ecb4b2b56adcae45d81e56c9aed5f7fbf8956017', @rol3, 'L26090101@zacatepec.tecnm.mx', 1 WHERE @demo = 1;

SET @ue1 = (SELECT id_usuario FROM usuarios WHERE username='26090101');

INSERT INTO estudiantes (id_usuario,matricula,apellido_paterno,apellido_materno,nombres,id_carrera,id_periodo_ingreso,tipo_ingreso,estado)
SELECT @ue1, '26090101', 'Cruz', 'Pineda', 'Lucía', @sis, @p2026, 'Regular', 'Inscrito' WHERE @demo = 1;

SET @e1 = (SELECT id_estudiante FROM estudiantes WHERE id_usuario=@ue1);

INSERT INTO usuarios (username,password_hash,id_rol,correo_institucional,activo)
SELECT '25090102', 'scrypt:32768:8:1$KwvkgaoOPqqsFmnl$ed25753aa5bd5c096e2fbdbfb7ce17d6760f1d19e11633dcb8f22cba39dd6e3e387e5397472361c42b68d1c877bf7c0207e31acfb43ef06d341223cf104cdda5', @rol3, 'L25090102@zacatepec.tecnm.mx', 1 WHERE @demo = 1;

SET @ue2 = (SELECT id_usuario FROM usuarios WHERE username='25090102');

INSERT INTO estudiantes (id_usuario,matricula,apellido_paterno,apellido_materno,nombres,id_carrera,id_periodo_ingreso,tipo_ingreso,estado)
SELECT @ue2, '25090102', 'Vega', 'Ríos', 'Mateo', @sis, @p2025, 'Regular', 'Inscrito' WHERE @demo = 1;

SET @e2 = (SELECT id_estudiante FROM estudiantes WHERE id_usuario=@ue2);

INSERT INTO usuarios (username,password_hash,id_rol,correo_institucional,activo)
SELECT '25090103', 'scrypt:32768:8:1$Fm7jPXnyX1asjVU3$072ecb6e179ba94592ce9a3739fc728349aedec563daaad44c12c14d52cba2e3ccf06d7ddb95833c50741df161bad2e50c400682fd01036427b9620b17f5b97c', @rol3, 'L25090103@zacatepec.tecnm.mx', 1 WHERE @demo = 1;

SET @ue3 = (SELECT id_usuario FROM usuarios WHERE username='25090103');

INSERT INTO estudiantes (id_usuario,matricula,apellido_paterno,apellido_materno,nombres,id_carrera,id_periodo_ingreso,tipo_ingreso,estado)
SELECT @ue3, '25090103', 'Lara', 'Solís', 'Elisa', @electro, @p2025, 'Regular', 'Inscrito' WHERE @demo = 1;

SET @e3 = (SELECT id_estudiante FROM estudiantes WHERE id_usuario=@ue3);

CREATE TEMPORARY TABLE tmp_horario_estudiante (id_estudiante INT, id_materia INT, dia_semana VARCHAR(12), id_bloque INT);
INSERT INTO tmp_horario_estudiante VALUES
(@e1, @m_ACA_0907, 'Lunes', @h7),
(@e1, @m_ACA_0907, 'Martes', @h7),
(@e1, @m_ACA_0907, 'Miércoles', @h7),
(@e1, @m_ACA_0907, 'Jueves', @h7),
(@e1, @m_ACC_0906, 'Lunes', @h8),
(@e1, @m_ACC_0906, 'Martes', @h8),
(@e1, @m_ACC_0906, 'Miércoles', @h8),
(@e1, @m_ACC_0906, 'Jueves', @h8),
(@e1, @m_ACF_0901, 'Lunes', @h9),
(@e1, @m_ACF_0901, 'Martes', @h9),
(@e1, @m_ACF_0901, 'Miércoles', @h9),
(@e1, @m_ACF_0901, 'Jueves', @h9),
(@e1, @m_ACF_0901, 'Viernes', @h9),
(@e1, @m_AED_1285, 'Lunes', @h10),
(@e1, @m_AED_1285, 'Martes', @h10),
(@e1, @m_AED_1285, 'Miércoles', @h10),
(@e1, @m_AED_1285, 'Jueves', @h10),
(@e1, @m_AED_1285, 'Viernes', @h10),
(@e1, @m_AEF_1041, 'Lunes', @h11),
(@e1, @m_AEF_1041, 'Martes', @h11),
(@e1, @m_AEF_1041, 'Miércoles', @h11),
(@e1, @m_AEF_1041, 'Jueves', @h11),
(@e1, @m_AEF_1041, 'Viernes', @h11),
(@e1, @m_SCH_1024, 'Lunes', @h12),
(@e1, @m_SCH_1024, 'Martes', @h12),
(@e1, @m_SCH_1024, 'Miércoles', @h12),
(@e1, @m_SCH_1024, 'Jueves', @h12),
(@e2, @m_ACD_0908, 'Lunes', @h7),
(@e2, @m_ACD_0908, 'Martes', @h7),
(@e2, @m_ACD_0908, 'Miércoles', @h7),
(@e2, @m_ACD_0908, 'Jueves', @h7),
(@e2, @m_ACD_0908, 'Viernes', @h7),
(@e2, @m_ACF_0904, 'Lunes', @h8),
(@e2, @m_ACF_0904, 'Martes', @h8),
(@e2, @m_ACF_0904, 'Miércoles', @h8),
(@e2, @m_ACF_0904, 'Jueves', @h8),
(@e2, @m_ACF_0904, 'Viernes', @h8),
(@e2, @m_AED_1026, 'Lunes', @h9),
(@e2, @m_AED_1026, 'Martes', @h9),
(@e2, @m_AED_1026, 'Miércoles', @h9),
(@e2, @m_AED_1026, 'Jueves', @h9),
(@e2, @m_AED_1026, 'Viernes', @h9),
(@e2, @m_SCC_1005, 'Lunes', @h10),
(@e2, @m_SCC_1005, 'Martes', @h10),
(@e2, @m_SCC_1005, 'Miércoles', @h10),
(@e2, @m_SCC_1005, 'Jueves', @h10),
(@e2, @m_SCC_1013, 'Lunes', @h11),
(@e2, @m_SCC_1013, 'Martes', @h11),
(@e2, @m_SCC_1013, 'Miércoles', @h11),
(@e2, @m_SCC_1013, 'Jueves', @h11),
(@e2, @m_SCF_1006, 'Lunes', @h12),
(@e2, @m_SCF_1006, 'Martes', @h12),
(@e2, @m_SCF_1006, 'Miércoles', @h12),
(@e2, @m_SCF_1006, 'Jueves', @h12),
(@e2, @m_SCF_1006, 'Viernes', @h12),
(@e3, @m_ACF_0904, 'Lunes', @h9),
(@e3, @m_ACF_0904, 'Martes', @h9),
(@e3, @m_ACF_0904, 'Miércoles', @h9),
(@e3, @m_ACF_0904, 'Jueves', @h9),
(@e3, @m_ACF_0904, 'Viernes', @h9),
(@e3, @m_AEE_1051, 'Lunes', @h10),
(@e3, @m_AEE_1051, 'Martes', @h10),
(@e3, @m_AEE_1051, 'Miércoles', @h10),
(@e3, @m_AEE_1051, 'Jueves', @h10),
(@e3, @m_EMC_1011, 'Lunes', @h11),
(@e3, @m_EMC_1011, 'Martes', @h11),
(@e3, @m_EMC_1011, 'Miércoles', @h11),
(@e3, @m_EMC_1011, 'Jueves', @h11),
(@e3, @m_EMC_1022, 'Lunes', @h12),
(@e3, @m_EMC_1022, 'Martes', @h12),
(@e3, @m_EMC_1022, 'Miércoles', @h12),
(@e3, @m_EMC_1022, 'Jueves', @h12),
(@e3, @m_EME_1008, 'Lunes', @h7),
(@e3, @m_EME_1008, 'Martes', @h7),
(@e3, @m_EME_1008, 'Miércoles', @h7),
(@e3, @m_EME_1008, 'Jueves', @h7),
(@e3, @m_EMJ_1021, 'Lunes', @h8),
(@e3, @m_EMJ_1021, 'Martes', @h8),
(@e3, @m_EMJ_1021, 'Miércoles', @h8),
(@e3, @m_EMJ_1021, 'Jueves', @h8),
(@e3, @m_EMJ_1021, 'Viernes', @h8),
(@e3, @m_EMJ_1021, 'Lunes', @h14);
INSERT INTO horario_estudiante(id_estudiante,id_materia,dia_semana,id_bloque)
SELECT id_estudiante,id_materia,dia_semana,id_bloque FROM tmp_horario_estudiante WHERE @demo=1;
DROP TEMPORARY TABLE tmp_horario_estudiante;

CREATE TEMPORARY TABLE tmp_horario_docente (id_docente INT, id_carrera INT, id_materia INT, dia_semana VARCHAR(12), id_bloque INT);
INSERT INTO tmp_horario_docente VALUES
(@d1, @sis, @m_ACF_0901, 'Lunes', @h9),
(@d1, @sis, @m_ACF_0901, 'Martes', @h9),
(@d1, @sis, @m_ACF_0901, 'Miércoles', @h9),
(@d1, @sis, @m_ACF_0901, 'Jueves', @h9),
(@d1, @sis, @m_ACF_0901, 'Viernes', @h9),
(@d2, @sis, @m_AED_1285, 'Lunes', @h10),
(@d2, @sis, @m_AED_1285, 'Martes', @h10),
(@d2, @sis, @m_AED_1285, 'Miércoles', @h10),
(@d2, @sis, @m_AED_1285, 'Jueves', @h10),
(@d2, @sis, @m_AED_1285, 'Viernes', @h10),
(@d3, @sis, @m_ACF_0902, 'Lunes', @h8),
(@d3, @sis, @m_ACF_0902, 'Martes', @h8),
(@d3, @sis, @m_ACF_0902, 'Miércoles', @h8),
(@d3, @sis, @m_ACF_0902, 'Jueves', @h8),
(@d3, @sis, @m_ACF_0902, 'Viernes', @h8),
(@d4, @sis, @m_AED_1286, 'Lunes', @h11),
(@d4, @sis, @m_AED_1286, 'Martes', @h11),
(@d4, @sis, @m_AED_1286, 'Miércoles', @h11),
(@d4, @sis, @m_AED_1286, 'Jueves', @h11),
(@d4, @sis, @m_AED_1286, 'Viernes', @h11),
(@d5, @electro, @m_ACF_0904, 'Lunes', @h9),
(@d5, @electro, @m_ACF_0904, 'Martes', @h9),
(@d5, @electro, @m_ACF_0904, 'Miércoles', @h9),
(@d5, @electro, @m_ACF_0904, 'Jueves', @h9),
(@d5, @electro, @m_ACF_0904, 'Viernes', @h9),
(@d5, @sis, @m_ACF_0904, 'Lunes', @h8),
(@d5, @sis, @m_ACF_0904, 'Martes', @h8),
(@d5, @sis, @m_ACF_0904, 'Miércoles', @h8),
(@d5, @sis, @m_ACF_0904, 'Jueves', @h8),
(@d5, @sis, @m_ACF_0904, 'Viernes', @h8),
(@d6, @sis, @m_AED_1026, 'Lunes', @h9),
(@d6, @sis, @m_AED_1026, 'Martes', @h9),
(@d6, @sis, @m_AED_1026, 'Miércoles', @h9),
(@d6, @sis, @m_AED_1026, 'Jueves', @h9),
(@d6, @sis, @m_AED_1026, 'Viernes', @h9),
(@d7, @electro, @m_EMC_1011, 'Lunes', @h11),
(@d7, @electro, @m_EMC_1011, 'Martes', @h11),
(@d7, @electro, @m_EMC_1011, 'Miércoles', @h11),
(@d7, @electro, @m_EMC_1011, 'Jueves', @h11),
(@d8, @electro, @m_EMJ_1021, 'Lunes', @h8),
(@d8, @electro, @m_EMJ_1021, 'Lunes', @h14),
(@d8, @electro, @m_EMJ_1021, 'Martes', @h8),
(@d8, @electro, @m_EMJ_1021, 'Miércoles', @h8),
(@d8, @electro, @m_EMJ_1021, 'Jueves', @h8),
(@d8, @electro, @m_EMJ_1021, 'Viernes', @h8),
(@d9, @electro, @m_EMC_1018, 'Lunes', @h11),
(@d9, @electro, @m_EMC_1018, 'Martes', @h11),
(@d9, @electro, @m_EMC_1018, 'Miércoles', @h11),
(@d9, @electro, @m_EMC_1018, 'Jueves', @h11),
(@d9, @electro, @m_EMC_1018, 'Viernes', @h11);
INSERT INTO horario_docente(id_docente,id_carrera,id_materia,dia_semana,id_bloque)
SELECT id_docente,id_carrera,id_materia,dia_semana,id_bloque FROM tmp_horario_docente WHERE @demo=1;
DROP TEMPORARY TABLE tmp_horario_docente;

INSERT INTO tutor_materias(id_docente,id_materia,autorizada)
SELECT DISTINCT id_docente,id_materia,1 FROM v_materias_elegibles_tutor WHERE @demo=1;
SET @lunes = DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY);

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d1, @sis, @m_ACF_0901, DATE_ADD(@lunes,INTERVAL 0 DAY), @h15, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d3, @sis, @m_ACF_0901, DATE_ADD(@lunes,INTERVAL 0 DAY), @h15, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d5, @sis, @m_ACF_0904, DATE_ADD(@lunes,INTERVAL 1 DAY), @h15, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d6, @sis, @m_AED_1026, DATE_ADD(@lunes,INTERVAL 2 DAY), @h16, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d2, @sis, @m_AED_1285, DATE_ADD(@lunes,INTERVAL 2 DAY), @h15, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d4, @sis, @m_AED_1286, DATE_ADD(@lunes,INTERVAL 3 DAY), @h16, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d3, @sis, @m_ACF_0902, DATE_ADD(@lunes,INTERVAL 1 DAY), @h16, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d5, @electro, @m_ACF_0904, DATE_ADD(@lunes,INTERVAL 1 DAY), @h16, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d7, @electro, @m_EMC_1011, DATE_ADD(@lunes,INTERVAL 2 DAY), @h15, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d8, @electro, @m_EMJ_1021, DATE_ADD(@lunes,INTERVAL 3 DAY), @h16, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d5, @electro, @m_ACF_0901, DATE_ADD(@lunes,INTERVAL 4 DAY), @h15, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d1, @sis, @m_ACF_0901, DATE_ADD(@lunes,INTERVAL 3 DAY), @h10, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d9, @electro, @m_EME_1029, DATE_ADD(@lunes,INTERVAL 3 DAY), @h15, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d6, @sis, @m_AED_1285, DATE_ADD(@lunes,INTERVAL 4 DAY), @h16, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d1, @sis, @m_ACF_0901, DATE_ADD(@lunes,INTERVAL 7 DAY), @h15, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d3, @sis, @m_ACF_0901, DATE_ADD(@lunes,INTERVAL 7 DAY), @h15, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d5, @sis, @m_ACF_0904, DATE_ADD(@lunes,INTERVAL 8 DAY), @h15, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d6, @sis, @m_AED_1026, DATE_ADD(@lunes,INTERVAL 9 DAY), @h16, 10 WHERE @demo = 1;

SET @f18 = LAST_INSERT_ID();

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d2, @sis, @m_AED_1285, DATE_ADD(@lunes,INTERVAL 9 DAY), @h15, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d4, @sis, @m_AED_1286, DATE_ADD(@lunes,INTERVAL 10 DAY), @h16, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d3, @sis, @m_ACF_0902, DATE_ADD(@lunes,INTERVAL 8 DAY), @h16, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d5, @electro, @m_ACF_0904, DATE_ADD(@lunes,INTERVAL 8 DAY), @h16, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d7, @electro, @m_EMC_1011, DATE_ADD(@lunes,INTERVAL 9 DAY), @h15, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d8, @electro, @m_EMJ_1021, DATE_ADD(@lunes,INTERVAL 10 DAY), @h16, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d5, @electro, @m_ACF_0901, DATE_ADD(@lunes,INTERVAL 11 DAY), @h15, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d1, @sis, @m_ACF_0901, DATE_ADD(@lunes,INTERVAL 10 DAY), @h10, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d9, @electro, @m_EME_1029, DATE_ADD(@lunes,INTERVAL 10 DAY), @h15, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d6, @sis, @m_AED_1285, DATE_ADD(@lunes,INTERVAL 11 DAY), @h16, 10 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d1, @sis, @m_ACF_0901, DATE_ADD(@lunes,INTERVAL 8 DAY), @h17, 1 WHERE @demo = 1;

SET @f32 = LAST_INSERT_ID();

INSERT INTO reservas_asesoria (id_franja,id_estudiante,id_materia_inscrita,tipo_cita,id_reserva_origen,estado_cita,confirmada)
SELECT @f32, @e2, @m_ACF_0904, 'Inicial', NULL, 'Programada', 0 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d6, @sis, @m_AED_1026, DATE_ADD(@lunes,INTERVAL -5 DAY), @h16, 10 WHERE @demo = 1;

SET @f33 = LAST_INSERT_ID();

INSERT INTO reservas_asesoria (id_franja,id_estudiante,id_materia_inscrita,tipo_cita,id_reserva_origen,estado_cita,confirmada,resultado_atencion)
SELECT @f33, @e2, @m_AED_1026, 'Inicial', NULL, 'Realizada', 1, 'En seguimiento' WHERE @demo = 1;

SET @origen = LAST_INSERT_ID();

INSERT INTO acuerdos (id_reserva,descripcion_acuerdo,estado_acuerdo)
SELECT @origen, 'Practicar recorridos de listas enlazadas y revisar los resultados en la siguiente cita.', 'En seguimiento' WHERE @demo = 1;

INSERT INTO reservas_asesoria (id_franja,id_estudiante,id_materia_inscrita,tipo_cita,id_reserva_origen,estado_cita,confirmada)
SELECT @f18, @e2, @m_AED_1026, 'Seguimiento', @origen, 'Programada', 0 WHERE @demo = 1;

INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d7, @electro, @m_EMC_1011, DATE_ADD(@lunes,INTERVAL -4 DAY), @h15, 10 WHERE @demo = 1;

SET @f34 = LAST_INSERT_ID();

INSERT INTO reservas_asesoria (id_franja,id_estudiante,id_materia_inscrita,tipo_cita,id_reserva_origen,estado_cita,confirmada,resultado_atencion,anotaciones)
SELECT @f34,@e3,@m_EMC_1011,'Inicial',NULL,'Realizada',1,'Cerrado','Se resolvieron las dudas del ejercicio.' WHERE @demo=1;

-- Segunda franja del mismo tutor y materia posterior al seguimiento de Mateo.
INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo)
SELECT @d6,@sis,@m_AED_1026,DATE_ADD(@lunes,INTERVAL 10 DAY),@h17,10 WHERE @demo=1;

COMMIT;


SELECT * FROM estudiantes;
SELECT * FROM docentes;

USE tecnocontrol_escolar;

SET NAMES utf8mb4;
-- Insercion hacia la tabla roles
INSERT INTO roles (codigo_rol, nombre_actor) VALUES
('admin_escolar', 'Administrador Escolar'),
('coordinador_tutorias', 'Coordinador de Tutorías'),
('consulta_seguimiento', 'Tutor'),
('consulta_seguimiento_est', 'Estudiante');

-- Inserccion hacia la tabla periodos_escolares
INSERT INTO periodos_escolares (anio, ciclo, es_actual) VALUES
(2022, 'Agosto-Diciembre', 0),
(2026, 'Enero-Junio', 0),
(2026, 'Agosto-Diciembre', 1);

-- Inserccion hacia la tabla bloques_horarios
INSERT INTO bloques_horarios (hora_inicio, hora_fin, etiqueta) VALUES
('07:00:00', '08:00:00', '07:00-08:00'),
('08:00:00', '09:00:00', '08:00-09:00'),
('09:00:00', '10:00:00', '09:00-10:00'),
('10:00:00', '11:00:00', '10:00-11:00'),
('11:00:00', '12:00:00', '11:00-12:00'),
('12:00:00', '13:00:00', '12:00-13:00'),
('13:00:00', '14:00:00', '13:00-14:00'),
('14:00:00', '15:00:00', '14:00-15:00'),
('15:00:00', '16:00:00', '15:00-16:00'),
('16:00:00', '17:00:00', '16:00-17:00'),
('17:00:00', '18:00:00', '17:00-18:00'),
('18:00:00', '19:00:00', '18:00-19:00');

-- Inserccion departamentos
INSERT INTO departamentos (nombre) VALUES
('Sistemas y Computación'),
('Ciencias Básicas'),
('Ingeniería Industrial');

-- Inserccion carreras
INSERT INTO carreras (clave_oficial, nombre) VALUES
('ISIC-2010-224', 'Ingeniería en Sistemas Computacionales'),
('IIND-2010-227', 'Ingeniería Industrial');

-- Inserccion materias
INSERT INTO materias (clave_oficial, nombre, id_departamento, semestre_sugerido) VALUES
('ACF-0901', 'Cálculo Diferencial', 2, 1),
('ACF-0902', 'Cálculo Integral', 2, 2),
('AED-1285', 'Fundamentos de Programación', 1, 1),
('AEF-1041', 'Matemáticas Discretas', 1, 1),
('SCD-1008', 'Ingeniería de Software', 1, 6),
('SCA1034', 'Taller de Sistemas Operativos', 1, 6),
('ACA-0910', 'Taller de Investigación II', 1, 7),
('SCD-1015', 'Lenguajes y Autómatas I', 1, 6),
('SCC-1010', 'Graficación', 1, 5),
('CCD-2401', 'Fund. de Ciencia de Datos', 1, 8);

-- Inserccion carrera_metaria
INSERT INTO carrera_materia (id_carrera, id_materia) VALUES
(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10),
(2, 1), (2, 2);

-- Ingresar usuarios con contraseña hash
INSERT INTO usuarios (username, password_hash, id_rol, correo_institucional, activo) VALUES
('adminescolar0001', 'scrypt:32768:8:1$eCh1mgbCQsuHP42J$2b45e87687436c2a08000f83a457325cf0352bac20e9d914097b5f34a71708fb41d3f820c2a22f555e6d05fdab80d9fe0b2bb41ca8928c1000ad82eb7cf78a9b', 1, 'admin.escolar@zacatepec.tecnm.mx', 1),
('coordinadortutoria0001', 'scrypt:32768:8:1$8sb34XnVXEzyJNjq$d33ba2a986e1d9f5ef508d54f2abd9a7e2226cb1aaf0382c29758ca36f45c9cc084f5385ac9e4ffb9c0849ccb41bdd4ce0648a6da5040eeab3ed8fc5971b11f8', 2, 'tutorias@zacatepec.tecnm.mx', 1),
('maestro0001', 'scrypt:32768:8:1$B87lqyZ1y9Ap7tXg$ef2558d9b3719b619322e90381662d2c4f89b9db8e1db19e75aa5a42edd2e68bf26accc1b6597b87458aec8bf4fa72a1d9d91da98ea2345d9ace2867deb37c0f', 3, 'DVargas104@zacatepec.tecnm.mx', 1),
('maestro0002', 'scrypt:32768:8:1$WwVc8PdyVTOgpV29$a9cdb683122ed5b770e11084bfd71a3bd16d9bc11a51d5a0ee8dcdce0b454db45faa3708024a9797d36ca6fa37670f977e202ff6404d9fd00df94f06834af655', 3, 'JVega101@zacatepec.tecnm.mx', 1),
('maestro0003', 'scrypt:32768:8:1$fyDhQFQignZwKLz4$f3ad70f4f62bd9b24f67bf50face133c8f504c7e244d81347bcb544785a28d28a2ef224f430d0ab1d32a02ee2d3e59a3facaf1c892603d0c4a2cd7586ec9b0b4', 3, 'SLeon102@zacatepec.tecnm.mx', 1),
('maestro0004', 'scrypt:32768:8:1$3u4Ck6BlVNSpw0gG$b770adf619ff5946c137fc0fa930092b047d857a8fcfdb2a0fd075ab22176e7b89c767b91efc104f93153336e8b0ea5a787090b75dacae2a5073c4c65779ccdb', 3, 'DSantos103@zacatepec.tecnm.mx', 0),
('22090748', 'scrypt:32768:8:1$fTXfz5l7f1bY6INQ$67351354427df6a9476f1ba23449edc9a32a53a0309bfe021ebc835e407f2dbc15708b4816a4759701409e94057526fbaadba40580cd23f9ea1d0761d2562b97', 4, 'L22090748@zacatepec.tecnm.mx', 1),
('26090022', 'scrypt:32768:8:1$zOKMb2XW4IO9gl4O$56074ac4a9296f08ae10897bcb84cada0961686a35306ecf2e1c3aa3d9243148b2fae184236c723e7ee5903624b2efcc75276e0469a7dafa988962176d6e4fab', 4, 'L26090022@zacatepec.tecnm.mx', 1),
('26090023', 'scrypt:32768:8:1$FdwEaUPcploKjB1K$a369a485123a471aec8a13e7f2a62f943651c00a4596672a52c63b7571e70dcc88cb8abdadc4fffa460f82e1d2d39ab058e1853c64be0030b0932bc0a13d75c2', 4, 'L26090023@zacatepec.tecnm.mx', 1);

-- Insertar docentes
INSERT INTO docentes (id_usuario, clave_docente, apellido_paterno, apellido_materno, nombres, grado_academico, estado_laboral, id_departamento, habilitado_tutor) VALUES
(3, 'DOC-104', 'Vargas', 'León', 'Daniel', 'Mtro.', 'Activo', 1, 1),
(4, 'DOC-101', 'Vega', 'Soto', 'Julián', 'Mtro.', 'Activo', 2, 1),
(5, 'DOC-102', 'León', 'Ruiz', 'Sara', 'Mtra.', 'Activo', 2, 1),
(6, 'DOC-103', 'Santos', 'Cruz', 'David', 'Dr.', 'Investigación', 1, 0);

INSERT INTO tutor_materias (id_docente, id_materia) VALUES
(1, 5),
(2, 1),
(3, 2);

-- Insertar estudiantes
INSERT INTO estudiantes (id_usuario, matricula, apellido_paterno, apellido_materno, nombres, id_carrera, id_periodo_ingreso, tipo_ingreso, estado) VALUES
(7, '22090748', 'Salgado', 'Rivera', 'Luis Ivan', 1, 1, 'Regular', 'Inscrito'),
(8, '26090022', 'Cruz', 'Luna', 'Renata', 1, 3, 'Regular', 'Inscrito'),
(9, '26090023', 'Vera', 'Díaz', 'Miguel', 1, 3, 'Regular', 'Inscrito');

-- Insertar horario_estudiante
INSERT INTO horario_estudiante (id_estudiante, id_materia, dia_semana, id_bloque) VALUES
(1, 6, 'Lunes', 1), (1, 6, 'Lunes', 2),
(1, 7, 'Lunes', 3), (1, 7, 'Lunes', 4),
(1, 10, 'Lunes', 7), (1, 10, 'Lunes', 8),
(1, 9, 'Lunes', 9), (1, 9, 'Lunes', 10),
(1, 5, 'Martes', 1), (1, 5, 'Martes', 2),
(1, 8, 'Martes', 3), (1, 8, 'Martes', 4),
(1, 5, 'Miércoles', 2), (1, 8, 'Miércoles', 4), (1, 10, 'Miércoles', 7),
(1, 6, 'Jueves', 1), (1, 6, 'Jueves', 2),
(1, 7, 'Jueves', 3), (1, 7, 'Jueves', 4),
(1, 10, 'Jueves', 7), (1, 10, 'Jueves', 8),
(1, 9, 'Jueves', 9), (1, 9, 'Jueves', 10),
(1, 5, 'Viernes', 1), (1, 5, 'Viernes', 2),
(1, 8, 'Viernes', 3), (1, 8, 'Viernes', 4);

-- Continuacion de la carga para la tabla horario_estudiante
INSERT INTO horario_estudiante (id_estudiante, id_materia, dia_semana, id_bloque) VALUES
(2, 5, 'Martes', 1), (2, 5, 'Martes', 2), (2, 5, 'Miércoles', 2), (2, 5, 'Viernes', 1), (2, 5, 'Viernes', 2),
(3, 5, 'Martes', 1), (3, 5, 'Martes', 2), (3, 5, 'Miércoles', 2), (3, 5, 'Viernes', 1), (3, 5, 'Viernes', 2);

-- Inserccion datos horario_docente
INSERT INTO horario_docente (id_docente, id_carrera, id_materia, dia_semana, id_bloque) VALUES
(1, 1, 3, 'Lunes', 1),
(1, 1, 3, 'Miércoles', 3);

-- Franjas_asesorias, correccion de agotado
INSERT INTO franjas_asesoria (id_docente, id_carrera, id_materia, fecha, id_bloque, cupo_maximo, estado) VALUES
(1, 1, 5, '2026-11-20', 5, 10, 'Publicada'),
(1, 1, 5, '2026-11-24', 6, 10, 'Publicada'),
(1, 1, 5, '2026-11-25', 5, 10, 'Publicada');

-- Ivan pasa de 'Realizada' a 'Programada': la franja es el 20/11/2026 y aún no ocurre
INSERT INTO reservas_asesoria (id_franja, id_estudiante, tipo_cita, estado_cita) VALUES
(1, 2, 'Inicial', 'Programada'),
(1, 3, 'Inicial', 'Programada');

/* Consultas para confirmar que todo se haya registrado correctamente
SELECT COUNT(*) AS total_horarios FROM horario_estudiante;
SELECT * FROM franjas_asesoria;
SELECT * FROM reservas_asesoria;
*/



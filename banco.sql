create database testeInternalSistem;

create table usuario(
usuario_id	int primary key auto_increment,
nome		varchar(50),
sobrenome	varchar(50),
usuario		varchar(100),
senha		varchar(50),
estado		boolean
);

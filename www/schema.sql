-- init database

drop database if exists blog;

create database blog;

use blog;

grant select, insert, update, delete on blog.* to 'blog'@'localhost' identified by 'blog';

-- generating SQL for user:
create table `user` (
  `id` varchar(50) not null,
  `name` varchar(50) not null,
  `email` varchar(50) not null,
  `admin` bool not null,
  `passwd` varchar(50) not null,
  `created_at` real not null,
  `image` varchar(500) not null,
  unique key `idx_email` (`email`),
  primary key(`id`)
)engine=innodb default charset=utf8;
-- generating SQL for blog:
create table `blog` (
  `id` varchar(50) not null,
  `user_id` varchar(50) not null,
  `user_name` varchar(50) not null,
  `user_image` varchar(500) not null,
  `summary` varchar(200) not null,
  `name` varchar(50) not null,
  `content` text not null,
  `created_at` real not null,
  primary key(`id`)
)engine=innodb default charset=utf8;
-- generating SQL for comment:
create table `comment` (
  `id` varchar(50) not null,
  `user_id` varchar(50) not null,
  `user_name` varchar(50) not null,
  `user_image` varchar(500) not null,
  `blog_id` varchar(50) not null,
  `content` text not null,
  `created_at` real not null,
  primary key(`id`)
)engine=innodb default charset=utf8;

insert into user (`id`, `email`, `passwd`, `admin`, `name`, `created_at`) values ('0010018336417540987fff4508f43fbaed718e263442526000', 'admin@example.com', '5f4dcc3b5aa765d61d8327deb882cf99', 1, 'Administrator', 1402909113.628);

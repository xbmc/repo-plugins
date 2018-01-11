/*
 Navicat Premium Data Transfer

 Source Server         : Kodi MediathekView
 Source Server Type    : SQLite
 Source Server Version : 3012001
 Source Database       : main

 Target Server Type    : SQLite
 Target Server Version : 3012001
 File Encoding         : utf-8

 Date: 12/27/2017 23:56:51 PM
*/

PRAGMA foreign_keys = false;

-- ----------------------------
--  Table structure for channel
-- ----------------------------
DROP TABLE IF EXISTS "channel";
CREATE TABLE "channel" (
	 "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	 "dtCreated" integer(11,0) NOT NULL DEFAULT 0,
	 "touched" integer(1,0) NOT NULL DEFAULT 1,
	 "channel" TEXT(255,0) NOT NULL
);

-- ----------------------------
--  Table structure for film
-- ----------------------------
DROP TABLE IF EXISTS "film";
CREATE TABLE "film" (
	 "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	 "dtCreated" integer(11,0) NOT NULL DEFAULT 0,
	 "touched" integer(1,0) NOT NULL DEFAULT 1,
	 "channelid" INTEGER(11,0) NOT NULL,
	 "showid" INTEGER(11,0) NOT NULL,
	 "title" TEXT(255,0) NOT NULL,
	 "search" TEXT(255,0) NOT NULL,
	 "aired" integer(11,0),
	 "duration" integer(11,0),
	 "size" integer(11,0),
	 "description" TEXT(2048,0),
	 "website" TEXT(384,0),
	 "url_sub" TEXT(384,0),
	 "url_video" TEXT(384,0),
	 "url_video_sd" TEXT(384,0),
	 "url_video_hd" TEXT(384,0),
	CONSTRAINT "FK_FilmShow" FOREIGN KEY ("showid") REFERENCES "show" ("id") ON DELETE CASCADE,
	CONSTRAINT "FK_FilmChannel" FOREIGN KEY ("channelid") REFERENCES "channel" ("id") ON DELETE CASCADE
);

-- ----------------------------
--  Table structure for show
-- ----------------------------
DROP TABLE IF EXISTS "show";
CREATE TABLE "show" (
	 "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	 "dtCreated" integer(11,0) NOT NULL DEFAULT 0,
	 "touched" integer(1,0) NOT NULL DEFAULT 1,
	 "channelid" INTEGER(11,0) NOT NULL DEFAULT 0,
	 "show" TEXT(255,0) NOT NULL,
	 "search" TEXT(255,0) NOT NULL,
	CONSTRAINT "FK_ShowChannel" FOREIGN KEY ("channelid") REFERENCES "channel" ("id") ON DELETE CASCADE
);

-- ----------------------------
--  Table structure for status
-- ----------------------------
DROP TABLE IF EXISTS "status";
CREATE TABLE "status" (
	 "modified" integer(11,0),
	 "status" TEXT(32,0),
	 "lastupdate" integer(11,0),
	 "filmupdate" integer(11,0),
	 "fullupdate" integer(1,0),
	 "add_chn" integer(11,0),
	 "add_shw" integer(11,0),
	 "add_mov" integer(11,0),
	 "del_chm" integer(11,0),
	 "del_shw" integer(11,0),
	 "del_mov" integer(11,0),
	 "tot_chn" integer(11,0),
	 "tot_shw" integer(11,0),
	 "tot_mov" integer(11,0)
);

-- ----------------------------
--  Indexes structure for table film
-- ----------------------------
CREATE INDEX "dupecheck" ON film ("channelid", "showid", "url_video");
CREATE INDEX "index_1" ON film ("channelid", "title" COLLATE NOCASE);
CREATE INDEX "index_2" ON film ("showid", "title" COLLATE NOCASE);

-- ----------------------------
--  Indexes structure for table show
-- ----------------------------
CREATE INDEX "category" ON show ("category");
CREATE INDEX "search" ON show ("search");
CREATE INDEX "combined_1" ON show ("channelid", "search");
CREATE INDEX "combined_2" ON show ("channelid", "show");

PRAGMA foreign_keys = true;

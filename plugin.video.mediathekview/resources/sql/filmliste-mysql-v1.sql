-- MySQL dump 10.13  Distrib 5.7.20, for osx10.13 (x86_64)
--
-- Host: localhost    Database: filmliste
-- ------------------------------------------------------
-- Server version	5.7.20

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `filmliste`
--

/*!40000 DROP DATABASE IF EXISTS `filmliste`*/;

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `filmliste` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `filmliste`;

--
-- Table structure for table `channel`
--

DROP TABLE IF EXISTS `channel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `channel` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dtCreated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `touched` smallint(1) NOT NULL DEFAULT '1',
  `channel` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `channel` (`channel`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `film`
--

DROP TABLE IF EXISTS `film`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `film` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dtCreated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `touched` smallint(1) NOT NULL DEFAULT '1',
  `channelid` int(11) NOT NULL,
  `showid` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `search` varchar(255) NOT NULL,
  `aired` timestamp NULL DEFAULT NULL,
  `duration` time DEFAULT NULL,
  `size` int(11) DEFAULT NULL,
  `description` longtext,
  `website` varchar(384) DEFAULT NULL,
  `url_sub` varchar(384) DEFAULT NULL,
  `url_video` varchar(384) DEFAULT NULL,
  `url_video_sd` varchar(384) DEFAULT NULL,
  `url_video_hd` varchar(384) DEFAULT NULL,
  `airedepoch` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `index_1` (`showid`,`title`),
  KEY `index_2` (`channelid`,`title`),
  KEY `dupecheck` (`channelid`,`showid`,`url_video`),
  CONSTRAINT `FK_FilmChannel` FOREIGN KEY (`channelid`) REFERENCES `channel` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION,
  CONSTRAINT `FK_FilmShow` FOREIGN KEY (`showid`) REFERENCES `show` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `show`
--

DROP TABLE IF EXISTS `show`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `show` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dtCreated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `touched` smallint(1) NOT NULL DEFAULT '1',
  `channelid` int(11) NOT NULL,
  `show` varchar(255) NOT NULL,
  `search` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `show` (`show`),
  KEY `search` (`search`),
  KEY `combined_1` (`channelid`,`search`),
  KEY `combined_2` (`channelid`,`show`),
  CONSTRAINT `FK_ShowChannel` FOREIGN KEY (`channelid`) REFERENCES `channel` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `status`
--

DROP TABLE IF EXISTS `status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `status` (
  `modified` int(11) NOT NULL,
  `status` varchar(255) NOT NULL,
  `lastupdate` int(11) NOT NULL,
  `filmupdate` int(11) NOT NULL,
  `fullupdate` int(1) NOT NULL,
  `add_chn` int(11) NOT NULL,
  `add_shw` int(11) NOT NULL,
  `add_mov` int(11) NOT NULL,
  `del_chm` int(11) NOT NULL,
  `del_shw` int(11) NOT NULL,
  `del_mov` int(11) NOT NULL,
  `tot_chn` int(11) NOT NULL,
  `tot_shw` int(11) NOT NULL,
  `tot_mov` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `status`
--

LOCK TABLES `status` WRITE;
/*!40000 ALTER TABLE `status` DISABLE KEYS */;
INSERT INTO `status` VALUES (0,'IDLE',0,0,0,0,0,0,0,0,0,0,0,0);
/*!40000 ALTER TABLE `status` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'filmliste'
--
/*!50003 DROP PROCEDURE IF EXISTS `ftInsertChannel` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ftInsertChannel`(
	_channel	VARCHAR(255)
)
BEGIN
	DECLARE	channelid_	INT(11);
	DECLARE	touched_	INT(1);
	DECLARE added_		INT(1) DEFAULT 0;

	SELECT	`id`,
			`touched`
	INTO	channelid_,
			touched_
	FROM	`channel`
	WHERE	( `channel`.`channel` = _channel );

	IF ( channelid_ IS NULL ) THEN
		INSERT INTO `channel` (
			`channel`
		)
		VALUES (
			_channel
		);
		SET channelid_	= LAST_INSERT_ID();
		SET added_ = 1;
	ELSE
		UPDATE	`channel`
		SET		`touched` = 1
		WHERE	( `id` = channelid_ );
	END IF;

	SELECT	channelid_	AS `id`,
			added_		AS `added`;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ftInsertFilm` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ftInsertFilm`(
	_channelid		INT(11),
	_showid			INT(11),
	_title			VARCHAR(255),
	_search			VARCHAR(255),
	_aired			TIMESTAMP,
	_duration		TIME,
	_size			INT(11),
	_description	LONGTEXT,
	_website		VARCHAR(384),
	_url_sub		VARCHAR(384),
	_url_video		VARCHAR(384),
	_url_video_sd	VARCHAR(384),
	_url_video_hd	VARCHAR(384),
	_airedepoch		INT(11)
)
BEGIN
	DECLARE		id_			INT;
	DECLARE		added_		INT DEFAULT 0;

	SELECT		`id`
	INTO		id_
	FROM		`film` AS f
	WHERE		( f.channelid = _channelid )
				AND
				( f.showid = _showid )
				AND
				( f.url_video = _url_video );

	IF ( id_ IS NULL ) THEN
		INSERT INTO `film` (
			`channelid`,
			`showid`,
			`title`,
			`search`,
			`aired`,
			`duration`,
			`size`,
			`description`,
			`website`,
			`url_sub`,
			`url_video`,
			`url_video_sd`,
			`url_video_hd`,
			`airedepoch`
		)
		VALUES (
			_channelid,
			_showid,
			_title,
			_search,
			IF(_aired = "1980-01-01 00:00:00", NULL, _aired),
			IF(_duration = "00:00:00", NULL, _duration),
			_size,
			_description,
			_website,
			_url_sub,
			_url_video,
			_url_video_sd,
			_url_video_hd,
			_airedepoch
		);
		SET id_			= LAST_INSERT_ID();
		SET added_		= 1;
	ELSE
		UPDATE	`film`
		SET		`touched` = 1
		WHERE	( `id` = id_ );
	END IF;
	SELECT	id_			AS `id`,
			added_		AS `added`;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ftInsertShow` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ftInsertShow`(
	_channelid	INT(11),
	_show		VARCHAR(255),
	_search		VARCHAR(255)
)
BEGIN
	DECLARE	showid_		INT(11);
	DECLARE	touched_	INT(1);
	DECLARE added_		INT(1) DEFAULT 0;

	SELECT	`id`,
			`touched`
	INTO	showid_,
			touched_
	FROM	`show`
	WHERE	( `show`.`channelid` = _channelid )
			AND
			( `show`.`show` = _show );

	IF ( showid_ IS NULL ) THEN
		INSERT INTO `show` (
			`channelid`,
			`show`,
			`search`
		)
		VALUES (
			_channelid,
			_show,
			_search
		);
		SET showid_	= LAST_INSERT_ID();
		SET added_ = 1;
	ELSE
		UPDATE	`show`
		SET		`touched` = 1
		WHERE	( `id` = showid_ );
	END IF;


	SELECT	showid_		AS `id`,
			added_		AS `added`;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ftUpdateEnd` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ftUpdateEnd`(
	_full	INT(1)
)
BEGIN
	DECLARE		del_chn_		INT DEFAULT 0;
	DECLARE		del_shw_		INT DEFAULT 0;
	DECLARE		del_mov_		INT DEFAULT 0;
	DECLARE		cnt_chn_		INT DEFAULT 0;
	DECLARE		cnt_shw_		INT DEFAULT 0;
	DECLARE		cnt_mov_		INT DEFAULT 0;

	IF ( _full = 1 ) THEN
		SELECT		COUNT(*)
		INTO		del_chn_
		FROM		`channel`
		WHERE		( `touched` = 0 );

		SELECT		COUNT(*)
		INTO		del_shw_
		FROM		`show`
		WHERE		( `touched` = 0 );

		SELECT		COUNT(*)
		INTO		del_mov_
		FROM		`film`
		WHERE		( `touched` = 0 );

		DELETE FROM	`show`
		WHERE		( `show`.`touched` = 0 )
					AND
					( ( SELECT SUM( `film`.`touched` ) FROM `film` WHERE `film`.`showid` = `show`.`id` ) = 0 );

		DELETE FROM	`film`
		WHERE		( `touched` = 0 );
	ELSE
		SET del_chn_ = 0;
		SET del_shw_ = 0;
		SET del_mov_ = 0;
	END IF;

	SELECT	del_chn_	AS	`del_chn`,
			del_shw_	AS	`del_shw`,
			del_mov_	AS	`del_mov`,
			cnt_chn_	AS	`cnt_chn`,
			cnt_shw_	AS	`cnt_shw`,
			cnt_mov_	AS	`cnt_mov`;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ftUpdateStart` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ftUpdateStart`(
	_full	INT(1)
)
BEGIN
	DECLARE		cnt_chn_		INT DEFAULT 0;
	DECLARE		cnt_shw_		INT DEFAULT 0;
	DECLARE		cnt_mov_		INT DEFAULT 0;

	IF ( _full = 1 ) THEN
		UPDATE	`channel`
		SET		`touched` = 0;

		UPDATE	`show`
		SET		`touched` = 0;

		UPDATE	`film`
		SET		`touched` = 0;
	END IF;

	SELECT	COUNT(*)
	INTO	cnt_chn_
	FROM	`channel`;

	SELECT	COUNT(*)
	INTO	cnt_shw_
	FROM	`show`;

	SELECT	COUNT(*)
	INTO	cnt_mov_
	FROM	`film`;

	SELECT	cnt_chn_	AS `cnt_chn`,
			cnt_shw_	AS `cnt_shw`,
			cnt_mov_	AS `cnt_mov`;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2018-01-03 16:26:35

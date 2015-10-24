-- phpMyAdmin SQL Dump
-- version 4.4.10
-- http://www.phpmyadmin.net
--
-- Host: localhost:3306
-- Generation Time: Oct 20, 2015 at 01:17 AM
-- Server version: 5.5.42
-- PHP Version: 5.6.10

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

--
-- Database: `pet_game`
--

-- --------------------------------------------------------

--
-- Table structure for table `charge`
--

CREATE TABLE `charge` (
  `id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `administrator_id` bigint(20) NOT NULL,
  `face` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `score` bigint(20) NOT NULL,
  `time` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `gamble`
--

CREATE TABLE `gamble` (
  `id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `ex_type` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `ex_id` bigint(20) NOT NULL,
  `earning` bigint(20) NOT NULL,
  `time` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `gamble_fqzs`
--

CREATE TABLE `gamble_fqzs` (
  `id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `game_id` bigint(20) NOT NULL,
  `face` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `cost` bigint(20) NOT NULL,
  `earning` bigint(20) NOT NULL,
  `time_pay` bigint(20) NOT NULL,
  `time_earn` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `gamble_fqzs_game`
--

CREATE TABLE `gamble_fqzs_game` (
  `id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL COMMENT 'the user who starts this game',
  `face` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `time_start` bigint(20) NOT NULL DEFAULT '0',
  `time_end` bigint(20) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `gamble_ggl`
--

CREATE TABLE `gamble_ggl` (
  `id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `prize` int(11) NOT NULL,
  `cost` bigint(20) NOT NULL,
  `earning` bigint(20) NOT NULL,
  `time` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `gamble_sx`
--

CREATE TABLE `gamble_sx` (
  `id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `game_id` bigint(20) NOT NULL,
  `face` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `cost` bigint(20) NOT NULL,
  `earning` bigint(20) NOT NULL,
  `time_pay` bigint(20) NOT NULL,
  `time_earn` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `gamble_sx_game`
--

CREATE TABLE `gamble_sx_game` (
  `id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL COMMENT 'the user who starts this game',
  `number_big` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `number_small` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `time_start` bigint(20) NOT NULL DEFAULT '0',
  `time_end` bigint(20) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `level_up`
--

CREATE TABLE `level_up` (
  `id` bigint(20) NOT NULL,
  `pet_id` bigint(20) NOT NULL,
  `from_level` bigint(20) NOT NULL,
  `to_level` int(11) NOT NULL,
  `cost` bigint(20) NOT NULL,
  `time` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `monthcard`
--

CREATE TABLE `monthcard` (
  `id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `administrator_id` bigint(20) NOT NULL,
  `face` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `time_register` bigint(20) NOT NULL,
  `time_start` bigint(20) NOT NULL,
  `time_end` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `payment`
--

CREATE TABLE `payment` (
  `id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `ex_type` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `ex_id` bigint(20) NOT NULL,
  `value` bigint(20) NOT NULL,
  `time` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `pet`
--

CREATE TABLE `pet` (
  `id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `level` int(11) NOT NULL,
  `power` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `practice`
--

CREATE TABLE `practice` (
  `id` bigint(20) NOT NULL,
  `pet_id` bigint(20) NOT NULL,
  `earning` bigint(20) NOT NULL,
  `time` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sign_in`
--

CREATE TABLE `sign_in` (
  `id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `monthcard` bigint(20) DEFAULT NULL,
  `earning` bigint(20) NOT NULL,
  `time` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

CREATE TABLE `user` (
  `id` bigint(20) NOT NULL,
  `qq` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `admin_qq` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `group_nid` varchar(20) COLLATE utf8_unicode_ci NOT NULL,
  `score` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `work`
--

CREATE TABLE `work` (
  `id` bigint(20) NOT NULL,
  `pet_id` bigint(20) NOT NULL,
  `time_start` bigint(20) NOT NULL,
  `time_end` bigint(20) NOT NULL,
  `earning` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `charge`
--
ALTER TABLE `charge`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `gamble`
--
ALTER TABLE `gamble`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ex_type` (`ex_type`,`ex_id`);

--
-- Indexes for table `gamble_fqzs`
--
ALTER TABLE `gamble_fqzs`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `gamble_fqzs_game`
--
ALTER TABLE `gamble_fqzs_game`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `gamble_ggl`
--
ALTER TABLE `gamble_ggl`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `gamble_sx`
--
ALTER TABLE `gamble_sx`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `gamble_sx_game`
--
ALTER TABLE `gamble_sx_game`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `level_up`
--
ALTER TABLE `level_up`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `monthcard`
--
ALTER TABLE `monthcard`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `payment`
--
ALTER TABLE `payment`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ex_type` (`ex_type`,`ex_id`);

--
-- Indexes for table `pet`
--
ALTER TABLE `pet`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `practice`
--
ALTER TABLE `practice`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sign_in`
--
ALTER TABLE `sign_in`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_qq` (`qq`,`group_nid`) USING BTREE;

--
-- Indexes for table `work`
--
ALTER TABLE `work`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `charge`
--
ALTER TABLE `charge`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `gamble`
--
ALTER TABLE `gamble`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `gamble_fqzs`
--
ALTER TABLE `gamble_fqzs`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `gamble_fqzs_game`
--
ALTER TABLE `gamble_fqzs_game`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `gamble_ggl`
--
ALTER TABLE `gamble_ggl`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `gamble_sx`
--
ALTER TABLE `gamble_sx`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `gamble_sx_game`
--
ALTER TABLE `gamble_sx_game`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `level_up`
--
ALTER TABLE `level_up`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `monthcard`
--
ALTER TABLE `monthcard`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `payment`
--
ALTER TABLE `payment`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `pet`
--
ALTER TABLE `pet`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `practice`
--
ALTER TABLE `practice`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `sign_in`
--
ALTER TABLE `sign_in`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `user`
--
ALTER TABLE `user`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `work`
--
ALTER TABLE `work`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;
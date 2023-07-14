--

-- Create model Metric

--

CREATE TABLE
    `metric` (
        `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `tcp_state` bool NOT NULL,
        `tcp_latency` integer NOT NULL,
        `handshake_latency` integer NOT NULL,
        `clock` datetime(6) NOT NULL
    );

--

-- Create model Pool

--

CREATE TABLE
    `pool` (
        `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `pool_id_bech32` varchar(64) NOT NULL UNIQUE,
        `pool_id_hex` varchar(64) NOT NULL UNIQUE,
        `active_epoch_no` integer NOT NULL,
        `vrf_key_hash` varchar(64) NOT NULL UNIQUE,
        `margin` integer NOT NULL,
        `fixed_cost` varchar(64) NOT NULL,
        `pledge` varchar(64) NOT NULL,
        `reward_addr` varchar(64) NOT NULL,
        `meta_url` varchar(2048) NOT NULL,
        `meta_hash` varchar(64) NOT NULL,
        `meta_json_name` varchar(64) NOT NULL,
        `meta_json_ticker` varchar(24) NOT NULL,
        `meta_json_homepage` varchar(2048) NOT NULL,
        `meta_json_description` varchar(64) NOT NULL,
        `pool_status` varchar(10) NOT NULL,
        `retiring_epoch` integer NULL,
        `op_cert` varchar(64) NOT NULL,
        `op_cert_counter` integer NOT NULL,
        `active_stake` varchar(64) NOT NULL,
        `sigma` varchar(64) NOT NULL,
        `block_count` integer NOT NULL,
        `live_pledge` varchar(64) NOT NULL,
        `live_stake` varchar(64) NOT NULL,
        `live_delegators` integer NOT NULL,
        `live_saturation` varchar(64) NOT NULL
    );

--

-- Create model Relay

--

CREATE TABLE
    `relay` (
        `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `dns` varchar(2048) NOT NULL,
        `srv` varchar(2048) NOT NULL,
        `ipv4` char(39) NOT NULL,
        `ipv6` char(39) NOT NULL,
        `port` integer NOT NULL,
        `watcher_determined_state` varchar(64) NOT NULL,
        `pool_id` bigint NOT NULL
    );

--

-- Create model Owner

--

CREATE TABLE
    `owner` (
        `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `owner_address` varchar(64) NOT NULL,
        `pool_id` bigint NOT NULL
    );

ALTER TABLE `relay`
ADD
    CONSTRAINT `relay_pool_id_5251263b_fk_pool_id` FOREIGN KEY (`pool_id`) REFERENCES `pool` (`id`);

ALTER TABLE `owner`
ADD
    CONSTRAINT `owner_pool_id_4d62e5f9_fk_pool_id` FOREIGN KEY (`pool_id`) REFERENCES `pool` (`id`);
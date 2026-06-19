package com.yuaiagent.service;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;



/**
 * 业务服务启动类
 */
@SpringBootApplication
@ComponentScan(basePackages = {"com.yuaiagent.service", "com.yuaiagent.common"})
public class ServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(ServiceApplication.class, args);
    }
}

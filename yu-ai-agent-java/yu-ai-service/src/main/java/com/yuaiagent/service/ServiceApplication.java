package com.yuaiagent.service;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.scheduling.annotation.EnableScheduling;



/**
 * 业务服务启动类
 * eyJhbGciOiJIUzUxMiJ9.eyJ1c2VySWQiOjEsInVzZXJuYW1lIjoieGsiLCJzdWIiOiJ4ayIsImlhdCI6MTc4MjAyNDc3NSwiZXhwIjoxNzgyMTExMTc1fQ.zJyJgpA6ZgcdHUd5NCITddEb2HI0ycCL2q74oQ1pRRwWIIHyIAnJE-IsjInkjtMU4ouae5jvOnGFkcmvV6Pg_A
 */
@SpringBootApplication
@ComponentScan(basePackages = {"com.yuaiagent.service", "com.yuaiagent.common"})
@EnableScheduling
public class ServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(ServiceApplication.class, args);
    }
}

package com.yuaiagent.service;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;



/**
 * 业务服务启动类
 * eyJhbGciOiJIUzUxMiJ9.eyJ1c2VySWQiOjEsInVzZXJuYW1lIjoieGsiLCJzdWIiOiJ4ayIsImlhdCI6MTc4MTkzNDQyOSwiZXhwIjoxNzgyMDIwODI5fQ.EK5ejEEZP34JTRzo6qYm_T99yCDYxj0NET3wOSkSfhC_t3PADunwseR_D7XZ_OnHD8ShpZQqTzVUo-NW7p9MGw
 */
@SpringBootApplication
@ComponentScan(basePackages = {"com.yuaiagent.service", "com.yuaiagent.common"})
public class ServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(ServiceApplication.class, args);
    }
}

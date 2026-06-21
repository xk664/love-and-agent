# Spring Boot 开发指南

## 概述

本文档介绍 Spring Boot 框架的核心概念和最佳实践。

## 核心特性

### 1. 自动配置

Spring Boot 提供了自动配置功能，能够根据项目依赖自动配置 Spring 应用程序。

```java
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

### 2. 起步依赖

通过起步依赖简化 Maven 配置：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
```

### 3. 内嵌服务器

Spring Boot 内嵌了 Tomcat、Jetty 等服务器，无需单独部署 WAR 文件。

## RESTful API 设计

### 基本原则

1. 使用名词而非动词命名资源
2. 使用 HTTP 方法表示操作
3. 返回适当的状态码
4. 支持分页和过滤

### 示例代码

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }

    @PostMapping
    public User createUser(@RequestBody User user) {
        return userService.save(user);
    }
}
```

## 数据库集成

### JPA 配置

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/mydb
    username: root
    password: password
  jpa:
    hibernate:
      ddl-auto: update
    show-sql: true
```

### 实体定义

```java
@Entity
@Table(name = "users")
@Data
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String username;

    @Column(nullable = false)
    private String email;
}
```

## 安全性

### Spring Security 集成

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**").permitAll()
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(Customizer.withDefaults());
        return http.build();
    }
}
```

## 总结

Spring Boot 简化了 Spring 应用的开发和部署，是现代 Java 开发的首选框架。

---

*文档版本: 1.0*
*最后更新: 2026-06-20*

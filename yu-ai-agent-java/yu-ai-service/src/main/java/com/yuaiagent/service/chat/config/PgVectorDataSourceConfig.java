package com.yuaiagent.service.chat.config;

import com.zaxxer.hikari.HikariDataSource;
import org.apache.ibatis.session.SqlSessionFactory;
import org.mybatis.spring.SqlSessionFactoryBean;
import org.mybatis.spring.SqlSessionTemplate;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.transaction.PlatformTransactionManager;

import javax.sql.DataSource;

/**
 * PgVector 数据源配置
 * 用于连接 PostgreSQL/PgVector 向量数据库
 */
@Configuration
@MapperScan(basePackages = "com.yuaiagent.service.knowledge.pgvector.mapper", sqlSessionFactoryRef = "pgVectorSqlSessionFactory")
public class PgVectorDataSourceConfig {

    @Value("${spring.pgvector.driver-class-name}")
    private String driverClassName;

    @Value("${spring.pgvector.jdbc-url}")
    private String jdbcUrl;

    @Value("${spring.pgvector.username}")
    private String username;

    @Value("${spring.pgvector.password}")
    private String password;

    @Value("${spring.pgvector.minimum-idle:2}")
    private int minimumIdle;

    @Value("${spring.pgvector.maximum-pool-size:10}")
    private int maximumPoolSize;

    @Value("${spring.pgvector.idle-timeout:30000}")
    private long idleTimeout;

    @Value("${spring.pgvector.max-lifetime:1800000}")
    private long maxLifetime;

    @Value("${spring.pgvector.connection-timeout:30000}")
    private long connectionTimeout;

    /**
     * PgVector 数据源
     */
    @Bean(name = "pgVectorDataSource")
    public DataSource pgVectorDataSource() {
        HikariDataSource dataSource = new HikariDataSource();
        dataSource.setDriverClassName(driverClassName);
        dataSource.setJdbcUrl(jdbcUrl);
        dataSource.setUsername(username);
        dataSource.setPassword(password);
        dataSource.setMinimumIdle(minimumIdle);
        dataSource.setMaximumPoolSize(maximumPoolSize);
        dataSource.setIdleTimeout(idleTimeout);
        dataSource.setMaxLifetime(maxLifetime);
        dataSource.setConnectionTimeout(connectionTimeout);
        return dataSource;
    }

    /**
     * PgVector SqlSessionFactory
     */
    @Bean(name = "pgVectorSqlSessionFactory")
    public SqlSessionFactory pgVectorSqlSessionFactory(@Qualifier("pgVectorDataSource") DataSource dataSource) throws Exception {
        SqlSessionFactoryBean sessionFactory = new SqlSessionFactoryBean();
        sessionFactory.setDataSource(dataSource);
        sessionFactory.setMapperLocations(
                new PathMatchingResourcePatternResolver().getResources("classpath*:mapper/pgvector/*.xml")
        );
        // 设置实体类包路径
        sessionFactory.setTypeAliasesPackage("com.yuaiagent.service.knowledge.pgvector.model");
        return sessionFactory.getObject();
    }

    /**
     * PgVector SqlSessionTemplate
     */
    @Bean(name = "pgVectorSqlSessionTemplate")
    public SqlSessionTemplate pgVectorSqlSessionTemplate(@Qualifier("pgVectorSqlSessionFactory") SqlSessionFactory sqlSessionFactory) {
        return new SqlSessionTemplate(sqlSessionFactory);
    }

    /**
     * PgVector 事务管理器
     */
    @Bean(name = "pgVectorTransactionManager")
    public PlatformTransactionManager pgVectorTransactionManager(@Qualifier("pgVectorDataSource") DataSource dataSource) {
        return new DataSourceTransactionManager(dataSource);
    }
}

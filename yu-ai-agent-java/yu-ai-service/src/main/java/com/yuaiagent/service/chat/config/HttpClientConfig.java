package com.yuaiagent.service.chat.config;

import okhttp3.OkHttpClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.concurrent.TimeUnit;

/**
 * HTTP 客户端配置
 */
@Configuration
public class HttpClientConfig {

    private final PythonServiceConfig pythonServiceConfig;

    public HttpClientConfig(PythonServiceConfig pythonServiceConfig) {
        this.pythonServiceConfig = pythonServiceConfig;
    }

    /**
     * 创建 OkHttp 客户端
     */
    @Bean
    public OkHttpClient okHttpClient() {
        return new OkHttpClient.Builder()
                .connectTimeout(pythonServiceConfig.getConnectTimeout(), TimeUnit.MILLISECONDS)
                .readTimeout(pythonServiceConfig.getReadTimeout(), TimeUnit.MILLISECONDS)
                .writeTimeout(pythonServiceConfig.getWriteTimeout(), TimeUnit.MILLISECONDS)
                .retryOnConnectionFailure(true)
                .build();
    }

}

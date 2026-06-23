package com.yuaiagent.service.chat.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * Python 服务配置
 */
@Data
@Configuration
@ConfigurationProperties(prefix = "python.service")
public class PythonServiceConfig {

    /**
     * Python 服务基础地址
     */
    private String baseUrl = "http://localhost:8000";

    /**
     * 连接超时时间（毫秒）
     */
    private int connectTimeout = 5000;

    /**
     * 读取超时时间（毫秒）
     * SSE 流式对话需要较长超时，LLM 生成首个 token 可能耗时较久
     */
    private int readTimeout = 120000;

    /**
     * 写入超时时间（毫秒）
     */
    private int writeTimeout = 30000;

    /**
     * API 端点配置
     */
    private Endpoints endpoints = new Endpoints();

    @Data
    public static class Endpoints {
        /**
         * 同步对话端点
         */
        private String chatSync = "/internal/ai/love/chat/sync";

        /**
         * 流式对话端点
         */
        private String chatSse = "/internal/ai/love/chat/sse";

        /**
         * 智能体任务端点
         */
        private String agentRun = "/internal/agent/run";

        /**
         * 智能体取消端点
         */
        private String agentCancel = "/internal/agent/cancel";

        /**
         * 健康检查端点
         */
        private String health = "/internal/health";

        /**
         * 知识库文档向量化端点
         */
        private String knowledgeIndex = "/internal/knowledge/index";
    }

}

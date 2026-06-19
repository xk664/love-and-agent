package com.yuaiagent.common.config;

import com.yuaiagent.common.response.Result;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * 健康检查端点
 */
@Tag(name = "系统", description = "系统相关接口")
@RestController
public class HealthController {

    @Operation(summary = "健康检查")
    @GetMapping("/api/health")
    public Result<Map<String, Object>> health() {
        Map<String, Object> data = new HashMap<>();
        data.put("status", "UP");
        data.put("timestamp", LocalDateTime.now().toString());
        data.put("service", "yu-ai-agent-java");
        return Result.success(data);
    }
}

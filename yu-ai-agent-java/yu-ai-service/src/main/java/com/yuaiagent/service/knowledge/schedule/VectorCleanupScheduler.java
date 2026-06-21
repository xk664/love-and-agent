package com.yuaiagent.service.knowledge.schedule;

import com.yuaiagent.service.knowledge.service.KnowledgeDocumentService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 向量清理定时任务
 * 定期扫描已软删除但向量未清理的文档，删除对应的向量
 */
@Slf4j
@Component
@EnableScheduling
@RequiredArgsConstructor
public class VectorCleanupScheduler {

    private final KnowledgeDocumentService knowledgeDocumentService;

    /**
     * 每30分钟执行一次，清理孤立向量
     * cron表达式：秒 分 时 日 月 星期
     */
    @Scheduled(cron = "0 */30 * * * ?")
    public void cleanupOrphanVectors() {
        log.info("开始执行向量清理定时任务");

        try {
            int cleanedCount = knowledgeDocumentService.cleanupOrphanVectors();
            log.info("向量清理定时任务完成: 清理文档数={}", cleanedCount);
        } catch (Exception e) {
            log.error("向量清理定时任务执行异常", e);
        }
    }
}

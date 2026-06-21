package com.yuaiagent.service.knowledge.util;

import lombok.extern.slf4j.Slf4j;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

/**
 * 文件内容提取工具类
 * 支持 Markdown、PDF、TXT 文件的文本内容提取
 */
@Slf4j
@Component
public class FileContentExtractor {

    /**
     * 从文件中提取文本内容
     *
     * @param file     上传的文件
     * @param fileType 文件类型（markdown / pdf / txt）
     * @return 提取的文本内容
     */
    public String extractContent(MultipartFile file, String fileType) throws IOException {
        return switch (fileType) {
            case "markdown" -> extractMarkdown(file);
            case "pdf" -> extractPdf(file);
            case "txt" -> extractTxt(file);
            default -> throw new IllegalArgumentException("不支持的文件类型: " + fileType);
        };
    }

    /**
     * 根据文件扩展名识别文件类型
     *
     * @param filename 文件名
     * @return 文件类型（markdown / pdf / txt）
     */
    public String resolveFileType(String filename) {
        if (filename == null) {
            throw new IllegalArgumentException("文件名不能为空");
        }

        String lowerName = filename.toLowerCase();
        if (lowerName.endsWith(".md") || lowerName.endsWith(".markdown")) {
            return "markdown";
        } else if (lowerName.endsWith(".pdf")) {
            return "pdf";
        } else if (lowerName.endsWith(".txt")) {
            return "txt";
        } else {
            throw new IllegalArgumentException("不支持的文件格式，仅支持 .md / .pdf / .txt");
        }
    }

    /**
     * 从文件名提取标题（去掉扩展名）
     *
     * @param filename 文件名
     * @return 标题
     */
    public String extractTitle(String filename) {
        if (filename == null || filename.isEmpty()) {
            return "未命名文档";
        }

        // 去掉扩展名
        int lastDotIndex = filename.lastIndexOf('.');
        if (lastDotIndex > 0) {
            return filename.substring(0, lastDotIndex);
        }
        return filename;
    }

    /**
     * 提取 Markdown 文件内容
     */
    private String extractMarkdown(MultipartFile file) throws IOException {
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(file.getInputStream(), StandardCharsets.UTF_8))) {
            StringBuilder content = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                content.append(line).append("\n");
            }
            return content.toString().trim();
        }
    }

    /**
     * 提取 PDF 文件内容
     */
    private String extractPdf(MultipartFile file) throws IOException {
        try (PDDocument document = Loader.loadPDF(file.getBytes())) {
            PDFTextStripper stripper = new PDFTextStripper();
            return stripper.getText(document).trim();
        }
    }

    /**
     * 提取 TXT 文件内容
     */
    private String extractTxt(MultipartFile file) throws IOException {
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(file.getInputStream(), StandardCharsets.UTF_8))) {
            StringBuilder content = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                content.append(line).append("\n");
            }
            return content.toString().trim();
        }
    }

}

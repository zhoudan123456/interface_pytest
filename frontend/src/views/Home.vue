<template>
  <div class="home-container">
    <el-card class="welcome-card">
      <template #header>
        <div class="card-header">
          <el-icon :size="40"><Document /></el-icon>
          <h2>欢迎使用招标文件检查点验证工具</h2>
        </div>
      </template>

      <div class="welcome-content">
        <p>本工具基于智谱AI的语义理解能力，自动验证招标文件检查点的提取准确性</p>

        <el-steps :active="0" finish-status="success" class="steps">
          <el-step title="上传文件" description="上传招标文件(PDF)和投标文件(PDF)" />
          <el-step title="API提取" description="调用后端API提取检查点" />
          <el-step title="上传标注" description="上传Excel标注和JSON算法结果" />
          <el-step title="AI验证" description="智谱AI进行语义匹配验证" />
          <el-step title="生成报告" description="生成验证报告" />
        </el-steps>

        <div class="action-buttons">
          <el-button type="primary" size="large" @click="goToUpload">
            <el-icon class="el-icon--left"><Upload /></el-icon>
            开始验证
          </el-button>
          <el-button type="success" size="large" @click="goToBatch">
            <el-icon class="el-icon--left"><Files /></el-icon>
            批量执行
          </el-button>
        </div>
      </div>
    </el-card>

    <el-divider />

    <el-card class="feature-card">
      <template #header>
        <h3>功能特点</h3>
      </template>

      <el-row :gutter="20">
        <el-col :span="8">
          <div class="feature-item">
            <el-icon :size="30" color="#409eff"><MagicStick /></el-icon>
            <h4>AI语义匹配</h4>
            <p>基于智谱AI的深度语义理解能力，准确判断检查点是否匹配</p>
          </div>
        </el-col>

        <el-col :span="8">
          <div class="feature-item">
            <el-icon :size="30" color="#67c23a"><Timer /></el-icon>
            <h4>实时进度</h4>
            <p>WebSocket实时推送处理进度，无需刷新页面</p>
          </div>
        </el-col>

        <el-col :span="8">
          <div class="feature-item">
            <el-icon :size="30" color="#e6a23c"><Document /></el-icon>
            <h4>详细报告</h4>
            <p>生成详细的Markdown格式验证报告，支持下载</p>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Document, Upload, MagicStick, Timer, Files } from '@element-plus/icons-vue'

const router = useRouter()

function goToUpload() {
  router.push('/upload')
}

function goToBatch() {
  router.push('/batch')
}
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 15px;
}

.card-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.welcome-content {
  text-align: center;
  padding: 20px 0;
}

.welcome-content > p {
  font-size: 16px;
  color: #606266;
  margin-bottom: 30px;
}

.steps {
  margin: 40px 0;
}

.action-buttons {
  margin-top: 40px;
}

.feature-card h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
}

.feature-item {
  text-align: center;
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  transition: all 0.3s;
}

.feature-item:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.feature-item h4 {
  margin: 15px 0 10px 0;
  font-size: 16px;
}

.feature-item p {
  color: #909399;
  font-size: 14px;
  line-height: 1.6;
}
</style>

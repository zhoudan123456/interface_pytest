<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <h1>招标文件检查点验证工具</h1>
    </el-header>

    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ElContainer, ElHeader, ElMain } from 'element-plus'
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.app-header h1 {
  font-size: 20px;
  margin: 0;
}

.app-main {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
</style>

<template>
  <div class="file-uploader">
    <el-upload
      drag
      action="/api/v1/upload"
      :on-success="handleSuccess"
      :on-error="handleError"
      :before-upload="beforeUpload"
      :data="{ type }"
      :show-file-list="false"
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        拖拽文件到此处或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          {{ tipText }}
        </div>
      </template>
    </el-upload>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElUpload, ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

const props = defineProps<{
  fileType: 'excel' | 'json' | 'pdf'
}>()

const emit = defineEmits<{
  uploaded: [fileInfo: any]
}>()

const tipText = computed(() => {
  const typeMap = {
    excel: '支持 .xlsx 格式文件，文件大小不超过 50MB',
    json: '支持 .json 格式文件，文件大小不超过 50MB',
    pdf: '支持 .pdf、.docx 格式文件，文件大小不超过 50MB'
  }
  return typeMap[props.fileType]
})

function beforeUpload(file: File) {
  let isValidType = false

  if (props.fileType === 'excel') {
    isValidType = file.name.endsWith('.xlsx')
  } else if (props.fileType === 'json') {
    isValidType = file.name.endsWith('.json')
  } else if (props.fileType === 'pdf') {
    // 支持PDF和DOCX格式
    isValidType = file.name.endsWith('.pdf') || file.name.endsWith('.docx')
  }

  const isLt50M = file.size / 1024 / 1024 < 50

  if (!isValidType) {
    const extension = props.fileType === 'excel' ? '.xlsx' :
                      props.fileType === 'json' ? '.json' : '.pdf、.docx'
    ElMessage.error(`请上传 ${extension} 格式文件`)
    return false
  }
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过 50MB')
    return false
  }
  return true
}

function handleSuccess(response: any) {
  if (response.code === 200) {
    ElMessage.success('上传成功')
    emit('uploaded', response.data)
  }
}

function handleError() {
  ElMessage.error('上传失败')
}
</script>

<style scoped>
.file-uploader {
  width: 100%;
}

.el-icon--upload {
  font-size: 67px;
  color: #409eff;
  margin: 20px 0;
}

.el-upload__text {
  font-size: 14px;
  color: #606266;
}

.el-upload__tip {
  font-size: 12px;
  color: #909399;
  margin-top: 7px;
}
</style>

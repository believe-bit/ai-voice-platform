<!-- views/SystemManagementPage.vue -->
<template>
  <div class="system-management">
    <aside class="sidebar">
      <h3>系统管理菜单</h3>
      <nav>
        <ul>
          <li>
            <a :class="{ active: activeSection === 'users' }" @click="setActiveSection('users')">用户管理</a>
          </li>
          <li>
            <a :class="{ active: activeSection === 'permissions' }" @click="setActiveSection('permissions')">权限管理</a>
          </li>
          <li>
            <a :class="{ active: activeSection === 'analytics' }" @click="setActiveSection('analytics')">数据分析</a>
          </li>
        </ul>
      </nav>
    </aside>
    <main class="content">
      <!-- 用户管理 -->
      <div v-if="activeSection === 'users'">
        <h2>用户管理</h2>
        <nav class="sub-nav">
          <button
            :class="{ 'sub-nav-active': activeSubSection === 'info' }"
            @click="setActiveSubSection('info')"
          >
            用户信息
          </button>
          <button
            :class="{ 'sub-nav-active': activeSubSection === 'grouping' }"
            @click="setActiveSubSection('grouping')"
          >
            用户分组
          </button>
          <button
            :class="{ 'sub-nav-active': activeSubSection === 'permissions' }"
            @click="setActiveSubSection('permissions')"
          >
            权限控制
          </button>
          <button
            :class="{ 'sub-nav-active': activeSubSection === 'progress' }"
            @click="setActiveSubSection('progress')"
          >
            学习进度跟踪
          </button>
        </nav>
        <div class="sub-content">
          <!-- 用户信息 -->
          <div v-if="activeSubSection === 'info'">
            <h3>用户信息</h3>
            <button class="add-button" @click="openAddUserModal" :disabled="isLoadingGroups">添加用户</button>
            <p v-if="isLoadingGroups" class="loading">正在加载分组数据...</p>
            <p v-if="groupError" class="error">加载分组失败: {{ groupError }}</p>
            <p v-if="!isLoadingGroups && groups.length === 0" class="error">无可用分组，请先在“用户分组”中添加分组</p>
            <table class="user-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>用户名</th>
                  <th>角色</th>
                  <th>分组</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in users" :key="user.id">
                  <td>{{ user.id }}</td>
                  <td>{{ user.username }}</td>
                  <td>{{ user.role }}</td>
                  <td>{{ user.group || '无分组' }}</td>
                  <td>
                    <button @click="editUser(user)">编辑</button>
                    <button @click="deleteUser(user.id)">删除</button>
                  </td>
                </tr>
              </tbody>
            </table>
            <!-- 添加/编辑用户模态框 -->
            <div v-if="showAddUserModal || showEditUserModal" class="modal">
              <div class="modal-content">
                <h3>{{ showAddUserModal ? '添加用户' : '编辑用户' }}</h3>
                <form @submit.prevent="saveUser">
                  <label>
                    用户名:
                    <input v-model="currentUser.username" required />
                  </label>
                  <label>
                    角色:
                    <select v-model="currentUser.role" required>
                      <option value="Admin">管理员</option>
                      <option value="Teacher">教师</option>
                      <option value="Student">学生</option>
                    </select>
                  </label>
                  <label>
                    分组:
                    <select v-model="currentUser.group" :disabled="isLoadingGroups || groups.length === 0">
                      <option value="" :disabled="groups.length > 0">无分组</option>
                      <option v-for="group in groups" :key="group.id" :value="group.name">{{ group.name }}</option>
                    </select>
                    <p v-if="isLoadingGroups" class="loading">正在加载分组...</p>
                    <p v-if="groupError" class="error">加载分组失败: {{ groupError }}</p>
                    <p v-if="!isLoadingGroups && groups.length === 0" class="error">无可用分组，请先添加分组</p>
                  </label>
                  <div class="modal-actions">
                    <button type="submit" :disabled="isLoadingGroups || (!showEditUserModal && groups.length === 0)">保存</button>
                    <button type="button" @click="cancelUserModal">取消</button>
                  </div>
                </form>
              </div>
            </div>
          </div>
          <!-- 用户分组 -->
          <div v-if="activeSubSection === 'grouping'">
            <h3>用户分组</h3>
            <button class="add-button" @click="showAddGroupModal = true">添加分组</button>
            <p v-if="groupError" class="error">保存分组失败: {{ groupError }}</p>
            <table class="group-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>分组名称</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="group in groups" :key="group.id">
                  <td>{{ group.id }}</td>
                  <td>{{ group.name }}</td>
                  <td>
                    <button @click="editGroup(group)">编辑</button>
                    <button @click="deleteGroup(group.id)">删除</button>
                  </td>
                </tr>
              </tbody>
            </table>
            <!-- 添加/编辑分组模态框 -->
            <div v-if="showAddGroupModal || showEditGroupModal" class="modal">
              <div class="modal-content">
                <h3>{{ showAddGroupModal ? '添加分组' : '编辑分组' }}</h3>
                <form @submit.prevent="saveGroup">
                  <label>
                    分组名称:
                    <input v-model="currentGroup.name" required />
                  </label>
                  <div class="modal-actions">
                    <button type="submit">保存</button>
                    <button type="button" @click="cancelGroupModal">取消</button>
                  </div>
                </form>
              </div>
            </div>
          </div>
          <!-- 权限控制 -->
          <div v-if="activeSubSection === 'permissions'">
            <h3>权限控制</h3>
            <table class="permission-table">
              <thead>
                <tr>
                  <th>权限ID</th>
                  <th>分配给</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="assignment in assignments" :key="assignment.permission_id">
                  <td>{{ assignment.permission_id }}</td>
                  <td>{{ assignment.assigned_to }}</td>
                  <td>
                    <button @click="deleteAssignment(assignment.permission_id)">删除</button>
                  </td>
                </tr>
              </tbody>
            </table>
            <button class="add-button" @click="showAssignPermissionModal = true">分配权限</button>
            <!-- 分配权限模态框 -->
            <div v-if="showAssignPermissionModal" class="modal">
              <div class="modal-content">
                <h3>分配权限</h3>
                <form @submit.prevent="assignPermission">
                  <label>
                    权限:
                    <select v-model="newAssignment.permission_id" required>
                      <option v-for="permission in permissions" :key="permission.id" :value="permission.id">{{ permission.name }}</option>
                    </select>
                  </label>
                  <label>
                    分配给:
                    <select v-model="newAssignment.assigned_to" required>
                      <option v-for="user in users" :key="user.id" :value="user.username">{{ user.username }}</option>
                    </select>
                  </label>
                  <div class="modal-actions">
                    <button type="submit">保存</button>
                    <button type="button" @click="showAssignPermissionModal = false">取消</button>
                  </div>
                </form>
              </div>
            </div>
          </div>
          <!-- 学习进度跟踪 -->
          <div v-if="activeSubSection === 'progress'">
            <h3>学习进度跟踪</h3>
            <table class="progress-table">
              <thead>
                <tr>
                  <th>用户ID</th>
                  <th>用户名</th>
                  <th>进度</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in users" :key="user.id">
                  <td>{{ user.id }}</td>
                  <td>{{ user.username }}</td>
                  <td>
                    <div class="progress-bar">
                      <div :style="{ width: (progress[user.id]?.completion || 0) + '%' }"></div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <!-- 权限管理 -->
      <div v-if="activeSection === 'permissions'">
        <h2>权限管理</h2>
        <table class="permission-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>权限名称</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="permission in permissions" :key="permission.id">
              <td>{{ permission.id }}</td>
              <td>{{ permission.name }}</td>
            </tr>
            <tr v-if="permissionError">
              <td colspan="2" class="error">加载权限失败: {{ permissionError }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- 数据分析 -->
      <div v-if="activeSection === 'analytics'">
        <h2>数据分析</h2>
        <div class="analytics-content">
          <div class="chart-container">
            <h3>学员能力柱状图</h3>
            <canvas id="abilityChart"></canvas>
          </div>
          <div class="chart-container">
            <h3>错误高频词</h3>
            <ul class="error-words-list">
              <li v-for="[word, weight] in errorWords" :key="word" :style="{ fontSize: `${weight * 40 + 12}px` }">
                {{ word }} (权重: {{ weight.toFixed(2) }})
              </li>
            </ul>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import axios from 'axios';
import { Chart } from 'chart.js/auto';

export default {
  name: 'SystemManagementPage',
  data() {
    return {
      activeSection: 'users',
      activeSubSection: 'info',
      users: [],
      groups: [],
      permissions: [],
      assignments: [],
      progress: {},
      errorWords: [
        ['错误1', 0.5], ['错误2', 0.4], ['错误3', 0.3], ['错误4', 0.2], ['错误5', 0.1]
      ],
      showAddUserModal: false,
      showEditUserModal: false,
      showAddGroupModal: false,
      showEditGroupModal: false,
      showAssignPermissionModal: false,
      currentUser: { id: null, username: '', role: 'Student', group: '' },
      currentGroup: { id: null, name: '' },
      newAssignment: { permission_id: null, assigned_to: '' },
      isLoadingGroups: false,
      groupError: null,
      permissionError: null,
      userError: null
    };
  },
  async mounted() {
    await this.fetchGroups(); // 优先加载分组
    await this.fetchUsers();
    await this.fetchPermissions();
    this.fetchAssignments();
    this.fetchProgress();
    this.fetchErrorWords();
  },
  methods: {
    setActiveSection(section) {
      this.activeSection = section;
      if (section === 'users') {
        this.activeSubSection = 'info';
      }
    },
    setActiveSubSection(subSection) {
      this.activeSubSection = subSection;
    },
    async fetchUsers() {
      try {
        const response = await axios.get('http://localhost:5000/users');
        this.users = response.data || [];
        this.userError = null;
      } catch (error) {
        console.error('获取用户失败:', error);
        this.userError = error.message || '网络错误';
      }
    },
    async fetchGroups() {
      this.isLoadingGroups = true;
      this.groupError = null;
      try {
        const response = await axios.get('http://localhost:5000/groups');
        this.groups = response.data || [];
        console.log('分组数据:', this.groups); // 调试日志
      } catch (error) {
        console.error('获取分组失败:', error);
        this.groupError = error.message || '网络错误';
        this.groups = [];
      } finally {
        this.isLoadingGroups = false;
      }
    },
    async fetchPermissions() {
      try {
        const response = await axios.get('http://localhost:5000/permissions');
        this.permissions = response.data || [];
        this.permissionError = null;
      } catch (error) {
        console.error('获取权限失败:', error);
        this.permissionError = error.message || '网络错误';
      }
    },
    async fetchAssignments() {
      // 模拟获取权限分配数据
      this.assignments = [
        { permission_id: 1, assigned_to: 'user1' },
        { permission_id: 2, assigned_to: 'user2' }
      ];
    },
    async fetchProgress() {
      try {
        for (const user of this.users) {
          const response = await axios.get(`http://localhost:5000/progress/${user.id}`);
          this.$set(this.progress, user.id, response.data);
        }
      } catch (error) {
        console.error('获取进度失败:', error);
      }
    },
    async fetchErrorWords() {
      // 模拟错误高频词数据
      this.errorWords = [
        ['错误1', 0.5], ['错误2', 0.4], ['错误3', 0.3], ['错误4', 0.2], ['错误5', 0.1]
      ];
    },
    openAddUserModal() {
      if (this.isLoadingGroups) {
        alert('分组数据正在加载，请稍后重试');
        return;
      }
      if (this.groupError) {
        alert(`无法加载分组: ${this.groupError}，请检查后端服务`);
        return;
      }
      if (this.groups.length === 0 && !this.showEditUserModal) {
        alert('当前无可用分组，请先在“用户分组”中添加分组');
        return;
      }
      this.showAddUserModal = true;
    },
    editUser(user) {
      this.currentUser = { ...user };
      this.showEditUserModal = true;
    },
    async saveUser() {
      try {
        if (this.showAddUserModal) {
          await axios.post('http://localhost:5000/users', this.currentUser);
        } else {
          await axios.put(`http://localhost:5000/users/${this.currentUser.id}`, this.currentUser);
        }
        this.fetchUsers();
        this.cancelUserModal();
      } catch (error) {
        console.error('保存用户失败:', error);
        alert('保存用户失败: ' + (error.message || '网络错误'));
      }
    },
    async deleteUser(userId) {
      try {
        await axios.delete(`http://localhost:5000/users/${userId}`);
        this.fetchUsers();
      } catch (error) {
        console.error('删除用户失败:', error);
        alert('删除用户失败: ' + (error.message || '网络错误'));
      }
    },
    cancelUserModal() {
      this.showAddUserModal = false;
      this.showEditUserModal = false;
      this.currentUser = { id: null, username: '', role: 'Student', group: '' };
    },
    editGroup(group) {
      this.currentGroup = { ...group };
      this.showEditGroupModal = true;
    },
    async saveGroup() {
      try {
        if (this.showAddGroupModal) {
          await axios.post('http://localhost:5000/groups', this.currentGroup);
        } else {
          await axios.put(`http://localhost:5000/groups/${this.currentGroup.id}`, this.currentGroup);
        }
        await this.fetchGroups();
        this.groupError = null;
        this.cancelGroupModal();
      } catch (error) {
        console.error('保存分组失败:', error);
        this.groupError = error.message || '网络错误';
        alert('保存分组失败: ' + this.groupError);
      }
    },
    async deleteGroup(groupId) {
      try {
        await axios.delete(`http://localhost:5000/groups/${groupId}`);
        await this.fetchGroups();
        this.groupError = null;
      } catch (error) {
        console.error('删除分组失败:', error);
        this.groupError = error.message || '网络错误';
        alert('删除分组失败: ' + this.groupError);
      }
    },
    cancelGroupModal() {
      this.showAddGroupModal = false;
      this.showEditGroupModal = false;
      this.currentGroup = { id: null, name: '' };
    },
    async assignPermission() {
      try {
        await axios.post('http://localhost:5000/assign_permission', this.newAssignment);
        this.fetchAssignments();
        this.showAssignPermissionModal = false;
        this.newAssignment = { permission_id: null, assigned_to: '' };
      } catch (error) {
        console.error('分配权限失败:', error);
        alert('分配权限失败: ' + (error.message || '网络错误'));
      }
    },
    async deleteAssignment(permissionId) {
      // 模拟删除权限分配
      this.assignments = this.assignments.filter(a => a.permission_id !== permissionId);
    },
    initCharts() {
      const ctx = document.getElementById('abilityChart').getContext('2d');
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: ['发音', '词汇', '语法', '流利度'],
          datasets: [{
            label: '学员能力',
            data: [85, 70, 60, 75],
            backgroundColor: 'rgba(0, 123, 255, 0.5)',
            borderColor: 'rgba(0, 123, 255, 1)',
            borderWidth: 1
          }]
        },
        options: {
          scales: {
            y: {
              beginAtZero: true,
              max: 100
            }
          }
        }
      });
    }
  },
  watch: {
    activeSection(newSection) {
      if (newSection === 'analytics') {
        this.$nextTick(() => {
          this.initCharts();
        });
      }
    }
  }
};
</script>

<style scoped>
.system-management {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 250px;
  background-color: #f8f9fa;
  padding: 20px;
  border-right: 1px solid #dee2e6;
}

.sidebar h3 {
  margin-bottom: 20px;
  font-size: 1.2em;
  color: #333;
}

.sidebar ul {
  list-style-type: none;
  padding: 0;
}

.sidebar li {
  margin-bottom: 10px;
}

.sidebar a {
  text-decoration: none;
  color: #007bff;
  font-size: 1em;
  display: block;
  padding: 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.sidebar a:hover,
.sidebar a.active {
  background-color: #e9ecef;
  text-decoration: none;
}

.content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.content h2 {
  margin-bottom: 20px;
  font-size: 1.5em;
  color: #333;
}

.content h3 {
  margin-bottom: 15px;
  font-size: 1.2em;
  color: #333;
}

.content p {
  color: #666;
}

.sub-nav {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.sub-nav button {
  padding: 8px 16px;
  border: none;
  background-color: #f1f1f1;
  color: #333;
  font-size: 1em;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.sub-nav button:hover {
  background-color: #e0e0e0;
}

.sub-nav button.sub-nav-active {
  background-color: #007bff;
  color: #fff;
}

.sub-content {
  margin-top: 20px;
}

.add-button {
  padding: 8px 16px;
  background-color: #007bff;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 20px;
}

.add-button:hover {
  background-color: #0056b3;
}

.add-button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.user-table, .group-table, .permission-table, .progress-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}

.user-table th, .user-table td,
.group-table th, .group-table td,
.permission-table th, .permission-table td,
.progress-table th, .progress-table td {
  border: 1px solid #dee2e6;
  padding: 10px;
  text-align: left;
}

.user-table th, .group-table th, .permission-table th, .progress-table th {
  background-color: #f8f9fa;
}

.user-table button, .group-table button, .permission-table button {
  margin-right: 5px;
  padding: 5px 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.user-table button:first-child, .group-table button:first-child {
  background-color: #007bff;
  color: #fff;
}

.user-table button:last-child, .group-table button:last-child, .permission-table button {
  background-color: #dc3545;
  color: #fff;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  width: 400px;
}

.modal-content h3 {
  margin-bottom: 20px;
}

.modal-content form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.modal-content label {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.modal-content input, .modal-content select {
  padding: 8px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.modal-content select:disabled {
  background-color: #f1f1f1;
  cursor: not-allowed;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.modal-actions button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.modal-actions button:first-child {
  background-color: #007bff;
  color: #fff;
}

.modal-actions button:first-child:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.modal-actions button:last-child {
  background-color: #6c757d;
  color: #fff;
}

.progress-bar {
  width: 100%;
  background-color: #f1f1f1;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar div {
  height: 20px;
  background-color: #007bff;
  transition: width 0.3s;
}

.analytics-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chart-container {
  max-width: 600px;
}

.error-words-list {
  list-style: none;
  padding: 0;
}

.error-words-list li {
  margin-bottom: 10px;
}

.loading {
  color: #007bff;
  font-size: 0.9em;
  margin-bottom: 10px;
}

.error {
  color: #dc3545;
  font-size: 0.9em;
  margin-bottom: 10px;
}
</style>
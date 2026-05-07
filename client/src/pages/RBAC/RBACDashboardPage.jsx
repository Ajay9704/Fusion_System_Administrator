import React, { useState, useEffect } from 'react';
import {
  Container,
  Title,
  Paper,
  Tabs,
  Text,
  SimpleGrid,
  ThemeIcon,
  Loader,
  Alert,
} from '@mantine/core';
import {
  IconShield,
  IconUsers,
  IconUserCheck,
  IconSettings,
  IconBan,
  IconLock,
  IconLockOpen,
} from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';

import RoleManagementPanel from '../../components/RBAC/RoleManagementPanel';
import UserManagementPanel from '../../components/RBAC/UserManagementPanel';
import BlockingPanel from '../../components/RBAC/BlockingPanel';
import ConfigPanel from '../../components/RBAC/ConfigPanel';
import MyRolesPanel from '../../components/RBAC/MyRolesPanel';

import {
  getUserStatus,
  getBlockedUsers,
  getRoleConflicts,
  getRoleEligibility,
} from '../../services/rbacService';
import apiClient from '../../services/api';

function RBACDashboardPage() {
  const [activeTab, setActiveTab] = useState('roles');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    totalBlockedUsers: 0,
    totalRoles: 0,
    totalConflicts: 0,
    totalEligibilityRules: 0,
  });

  // Fetch stats on mount
  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);

      // Fetch all roles to get total count
      const rolesResponse = await apiClient.get('/view-roles/');
      const rolesData = rolesResponse.data;
      const totalRoles = rolesData.length || 0;

      // Fetch blocked users count
      const blockedData = await getBlockedUsers();
      const blockedCount = blockedData.success ? (blockedData.blocked_users?.length || 0) : 0;

      // Fetch conflicts count
      const conflictsData = await getRoleConflicts();
      const conflictsCount = Object.keys(conflictsData.role_conflicts || {}).length;

      // Fetch eligibility count
      const eligibilityData = await getRoleEligibility();
      const eligibilityCount = Object.keys(eligibilityData.role_eligibility || {}).length;

      setStats({
        totalBlockedUsers: blockedCount,
        totalRoles: totalRoles,
        totalConflicts: conflictsCount,
        totalEligibilityRules: eligibilityCount,
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
      showNotification({
        title: 'Error',
        message: 'Failed to load RBAC statistics',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container size="xl" py="xl">
      <Title order={1} mb="lg">
        RBAC Dashboard
      </Title>

      {/* Stats Cards */}
      <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} spacing="md" mb="xl">
        <Paper shadow="sm" p="md" radius="md" withBorder>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'sm' }}>
            <ThemeIcon variant="light" size="xl" color="blue">
              <IconShield size={24} />
            </ThemeIcon>
            <div>
              <Text size="xs" c="dimmed">Total Roles</Text>
              <Text size="xl" fw={700}>{stats.totalRoles}</Text>
            </div>
          </div>
        </Paper>

        <Paper shadow="sm" p="md" radius="md" withBorder>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'sm' }}>
            <ThemeIcon variant="light" size="xl" color="red">
              <IconBan size={24} />
            </ThemeIcon>
            <div>
              <Text size="xs" c="dimmed">Blocked Users</Text>
              <Text size="xl" fw={700} c="red">{stats.totalBlockedUsers}</Text>
            </div>
          </div>
        </Paper>

        <Paper shadow="sm" p="md" radius="md" withBorder>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'sm' }}>
            <ThemeIcon variant="light" size="xl" color="yellow">
              <IconLock size={24} />
            </ThemeIcon>
            <div>
              <Text size="xs" c="dimmed">Conflicts</Text>
              <Text size="xl" fw={700}>{stats.totalConflicts}</Text>
            </div>
          </div>
        </Paper>

        <Paper shadow="sm" p="md" radius="md" withBorder>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'sm' }}>
            <ThemeIcon variant="light" size="xl" color="green">
              <IconUserCheck size={24} />
            </ThemeIcon>
            <div>
              <Text size="xs" c="dimmed">Eligibility Rules</Text>
              <Text size="xl" fw={700}>{stats.totalEligibilityRules}</Text>
            </div>
          </div>
        </Paper>
      </SimpleGrid>

      {/* Main Content Tabs */}
      <Paper shadow="sm" radius="md" p="0">
        <Tabs value={activeTab} onChange={setActiveTab}>
          <Tabs.List>
            <Tabs.Tab
              value="roles"
              leftSection={<IconSettings size={16} />}
            >
              Role Management
            </Tabs.Tab>
            <Tabs.Tab
              value="users"
              leftSection={<IconUsers size={16} />}
            >
              User Management
            </Tabs.Tab>
            <Tabs.Tab
              value="blocking"
              leftSection={<IconLock size={16} />}
            >
              Blocking
            </Tabs.Tab>
            <Tabs.Tab
              value="config"
              leftSection={<IconSettings size={16} />}
            >
              Configuration
            </Tabs.Tab>
            <Tabs.Tab
              value="my-roles"
              leftSection={<IconUserCheck size={16} />}
            >
              My Roles
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="roles">
            <RoleManagementPanel onRefresh={fetchStats} />
          </Tabs.Panel>

          <Tabs.Panel value="users">
            <UserManagementPanel onRefresh={fetchStats} />
          </Tabs.Panel>

          <Tabs.Panel value="blocking">
            <BlockingPanel onRefresh={fetchStats} />
          </Tabs.Panel>

          <Tabs.Panel value="config">
            <ConfigPanel />
          </Tabs.Panel>

          <Tabs.Panel value="my-roles">
            <MyRolesPanel />
          </Tabs.Panel>
        </Tabs>
      </Paper>
    </Container>
  );
}

export default RBACDashboardPage;

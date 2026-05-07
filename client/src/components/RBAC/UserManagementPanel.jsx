import React, { useState, useEffect } from 'react';
import {
  Stack,
  Group,
  Text,
  TextInput,
  Select,
  Button,
  Paper,
  Table,
  Badge,
  ActionIcon,
  Modal,
  NumberInput,
  Alert,
  Loader,
  Title,
  Chip,
  Box,
} from '@mantine/core';
import {
  IconSearch,
  IconRefresh,
  IconShield,
  IconBan,
  IconLockOpen,
  IconUserCheck,
  IconTrash,
} from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';
import { rem } from '@mantine/core';

import {
  getUserRoles,
  assignRole,
  removeRole,
  replaceUserRoles,
  getUserStatus,
  blockUser,
  unblockUser,
} from '../../services/rbacService';
import { fetchUsersByType } from '../../services/userService';

function UserManagementPanel({ onRefresh }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [userRoles, setUserRoles] = useState([]);
  const [userRolesModal, setUserRolesModal] = useState(false);
  const [blockModal, setBlockModal] = useState(false);
  const [blockReason, setBlockReason] = useState('');

  // Available roles to assign
  const availableRoles = [
    { value: 'student', label: 'Student' },
    { value: 'faculty', label: 'Faculty' },
    { value: 'staff', label: 'Staff' },
    { value: 'hod', label: 'HOD' },
    { value: 'dean', label: 'Dean' },
    { value: 'director', label: 'Director' },
    { value: 'admin', label: 'Admin' },
  ];

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);

      // Fetch all user types using the correct API
      const [studentsResp, facultyResp, staffResp] = await Promise.all([
        fetch('http://localhost:8000/api/users?type=student', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
            'Content-Type': 'application/json',
          },
        }).catch(() => null),
        fetch('http://localhost:8000/api/users?type=faculty', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
            'Content-Type': 'application/json',
          },
        }).catch(() => null),
        fetch('http://localhost:8000/api/users?type=staff', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
            'Content-Type': 'application/json',
          },
        }).catch(() => null),
      ]);

      const processUsers = async (response, userType) => {
        if (!response || !response.ok) return [];
        const data = await response.json();
        return data.map(u => ({
          ...u,
          user_type: userType,
          username: u.username || u.user?.username || '',
          first_name: u.first_name || u.user?.first_name || '',
          last_name: u.last_name || u.user?.last_name || '',
          email: u.email || u.user?.email || '',
          user_status: 'ACTIVE', // Default status, will be updated below
        }));
      };

      const [students, faculty, staff] = await Promise.all([
        processUsers(studentsResp, 'student'),
        processUsers(facultyResp, 'faculty'),
        processUsers(staffResp, 'staff'),
      ]);

      let allUsers = [...students, ...faculty, ...staff];
      
      // OPTIMIZED: Don't fetch status for all users upfront
      // Status will be fetched on-demand when viewing specific user details
      console.log(`Fetched ${allUsers.length} users:`, allUsers.slice(0, 3));
      setUsers(allUsers);
    } catch (error) {
      console.error('Error fetching users:', error);
      showNotification({
        title: 'Error',
        message: 'Failed to load users',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleManageRoles = async (user) => {
    try {
      setLoading(true);
      const rolesData = await getUserRoles(user.username);

      setSelectedUser(user);
      setUserRoles(rolesData.roles || []);
      setUserRolesModal(true);
    } catch (error) {
      console.error('Error fetching user roles:', error);
      showNotification({
        title: 'Error',
        message: error.message || 'Failed to fetch user roles',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAssignRole = async (roleName) => {
    if (!selectedUser) return;

    try {
      setLoading(true);

      await assignRole(selectedUser.username, roleName);

      showNotification({
        title: 'Success',
        message: `Role '${roleName}' assigned to ${selectedUser.username}`,
        color: 'green',
      });

      // Refresh user roles
      await handleManageRoles(selectedUser);

      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Error assigning role:', error);
      showNotification({
        title: 'Error',
        message: error.message || 'Failed to assign role',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveRole = async (roleName) => {
    if (!selectedUser) return;

    if (userRoles.length <= 1) {
      showNotification({
        title: 'Error',
        message: 'Cannot remove last role. User must have at least one role.',
        color: 'red',
      });
      return;
    }

    try {
      setLoading(true);

      await removeRole(selectedUser.username, roleName);

      showNotification({
        title: 'Success',
        message: `Role '${roleName}' removed from ${selectedUser.username}`,
        color: 'green',
      });

      // Refresh user roles
      await handleManageRoles(selectedUser);

      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Error removing role:', error);
      showNotification({
        title: 'Error',
        message: error.message || 'Failed to remove role',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleBlockUser = (user) => {
    setSelectedUser(user);
    setBlockModal(true);
  };

  const handleConfirmBlock = async () => {
    if (!selectedUser || !blockReason.trim()) {
      showNotification({
        title: 'Error',
        message: 'Please provide a reason for blocking',
        color: 'red',
      });
      return;
    }

    try {
      setLoading(true);

      await blockUser(selectedUser.username, blockReason);

      showNotification({
        title: 'Success',
        message: `User '${selectedUser.username}' has been blocked`,
        color: 'green',
      });

      setBlockModal(false);
      setBlockReason('');
      setSelectedUser(null);

      await fetchUsers();
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Error blocking user:', error);
      
      // Extract error message from response
      const errorData = error.response?.data?.error;
      let errorMessage = 'Failed to block user';
      
      if (typeof errorData === 'object' && errorData !== null) {
        errorMessage = errorData.message || errorMessage;
      } else if (typeof errorData === 'string') {
        errorMessage = errorData;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      showNotification({
        title: 'Error',
        message: errorMessage,
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUnblockUser = async (user) => {
    try {
      setLoading(true);

      await unblockUser(user.username);

      showNotification({
        title: 'Success',
        message: `User '${user.username}' has been unblocked`,
        color: 'green',
      });

      await fetchUsers();
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Error unblocking user:', error);
      
      // Extract error message from response
      const errorData = error.response?.data?.error;
      let errorMessage = 'Failed to unblock user';
      
      if (typeof errorData === 'object' && errorData !== null) {
        errorMessage = errorData.message || errorMessage;
      } else if (typeof errorData === 'string') {
        errorMessage = errorData;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      showNotification({
        title: 'Error',
        message: errorMessage,
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  // Filter users based on search
  const filteredUsers = users.filter(user =>
    user.username?.toLowerCase().includes(search.toLowerCase()) ||
    user.first_name?.toLowerCase().includes(search.toLowerCase()) ||
    user.last_name?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Stack>
      <Group justify="space-between" mb="md">
        <Title order={3}>User Management</Title>
        <Button
          leftSection={<IconRefresh size={16} />}
          onClick={fetchUsers}
          loading={loading}
        >
          Refresh
        </Button>
      </Group>

      {/* Search */}
      <TextInput
        placeholder="Search users..."
        leftSection={<IconSearch size={16} />}
        value={search}
        onChange={(e) => setSearch(e.currentTarget.value)}
      />

      {/* Users Table */}
      <Paper shadow="xs" withBorder>
        <Table.ScrollContainer minWidth={800}>
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Username</Table.Th>
                <Table.Th>Name</Table.Th>
                <Table.Th>Type</Table.Th>
                <Table.Th>Roles</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th style={{ textAlign: 'right' }}>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {loading ? (
                <Table.Tr>
                  <Table.Td colSpan={7}>
                    <Stack align="center" p="xl">
                      <Loader />
                      <Text size="sm" c="dimmed">Loading users...</Text>
                    </Stack>
                  </Table.Td>
                </Table.Tr>
              ) : filteredUsers.length === 0 ? (
                <Table.Tr>
                  <Table.Td colSpan={7}>
                    <Text ta="center" c="dimmed" py="xl">
                      No users found
                    </Text>
                  </Table.Td>
                </Table.Tr>
              ) : (
                filteredUsers.map((user) => (
                  <Table.Tr key={user.username}>
                    <Table.Td>{user.username}</Table.Td>
                    <Table.Td>
                      {user.first_name} {user.last_name}
                    </Table.Td>
                    <Table.Td>
                      <Badge color={user.user_type === 'student' ? 'blue' : user.user_type === 'faculty' ? 'green' : 'orange'}>
                        {user.user_type?.toUpperCase()}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Button
                        size="xs"
                        variant="subtle"
                        onClick={() => handleManageRoles(user)}
                      >
                        View roles →
                      </Button>
                    </Table.Td>
                    <Table.Td>
                      {user.user_status === 'BLOCKED' ? (
                        <Badge color="red">BLOCKED</Badge>
                      ) : user.user_status === 'SUSPENDED' ? (
                        <Badge color="orange">SUSPENDED</Badge>
                      ) : (
                        <Badge color="green">ACTIVE</Badge>
                      )}
                    </Table.Td>
                    <Table.Td ta="right">
                      <Group gap="xs" justify="right">
                        <ActionIcon
                          color="blue"
                          variant="light"
                          onClick={() => handleManageRoles(user)}
                        >
                          <IconShield size={18} />
                        </ActionIcon>
                        {user.user_status === 'BLOCKED' ? (
                          <ActionIcon
                            color="green"
                            variant="light"
                            onClick={() => handleUnblockUser(user)}
                            title="Unblock User"
                          >
                            <IconLockOpen size={18} />
                          </ActionIcon>
                        ) : (
                          <ActionIcon
                            color="red"
                            variant="light"
                            onClick={() => handleBlockUser(user)}
                            title="Block User"
                          >
                            <IconBan size={18} />
                          </ActionIcon>
                        )}
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))
              )}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>
      </Paper>

      {/* User Roles Modal */}
      <Modal
        opened={userRolesModal}
        onClose={() => setUserRolesModal(false)}
        title={`Manage Roles - ${selectedUser?.username || 'User'}`}
        size="lg"
      >
        <Stack>
          {selectedUser && (
            <>
              <Alert mb="md">
                <Text size="sm">
                  <strong>User Type:</strong> {selectedUser.user_type?.toUpperCase()}
                </Text>
              </Alert>

              <Group grow mb="md">
                <Select
                  label="Assign New Role"
                  placeholder="Select role to assign"
                  data={availableRoles}
                  disabled={loading}
                  onChange={(value) => {
                    if (value) handleAssignRole(value);
                  }}
                />
              </Group>

              <Text weight={600} mb="xs">
                Current Roles ({userRoles.length})
              </Text>

              {userRoles.length === 0 ? (
                <Text c="dimmed" ta="center" py="md">
                  No roles assigned
                </Text>
              ) : (
                <Stack>
                  {userRoles.map((role) => (
                    <Group 
                      key={role.id} 
                      justify="space-between" 
                      p="xs" 
                      bg={role.role_type === 'temporary' ? 'orange.0' : 'gray.0'} 
                      radius="sm"
                      style={{
                        border: role.role_type === 'temporary' ? '2px solid #ff922b' : '1px solid #e9ecef'
                      }}
                    >
                      <Stack gap={4}>
                        <Group gap="xs">
                          <Text>
                            <strong>{role.name}</strong>
                            {role.full_name && ` (${role.full_name})`}
                          </Text>
                          {role.role_type === 'temporary' && (
                            <Badge 
                              color="orange" 
                              size="sm"
                              leftSection={<IconShield size={12} />}
                            >
                              {role.temporary_tag || 'TEMPORARY'}
                            </Badge>
                          )}
                          {role.role_type === 'permanent' && (
                            <Badge 
                              color="green" 
                              size="sm"
                            >
                              {role.permanent_tag || 'PERMANENT'}
                            </Badge>
                          )}
                        </Group>
                        {role.role_type === 'temporary' && role.time_remaining && (
                          <Text size="xs" c="orange.7" fw={500}>
                            ⏱️ Expires in: {role.time_remaining}
                          </Text>
                        )}
                        {role.role_type === 'temporary' && role.expires_at && (
                          <Text size="xs" c="dimmed">
                            Expiry: {new Date(role.expires_at).toLocaleString()}
                          </Text>
                        )}
                      </Stack>

                      {role.role_type === 'permanent' && userRoles.length > 1 && (
                        <ActionIcon
                          color="red"
                          variant="light"
                          onClick={() => handleRemoveRole(role.name)}
                          loading={loading}
                        >
                          <IconTrash size={16} />
                        </ActionIcon>
                      )}
                      {role.role_type === 'temporary' && (
                        <Text size="xs" c="orange.7" fw={500}>
                          Auto-expiring
                        </Text>
                      )}
                    </Group>
                  ))}
                </Stack>
              )}
            </>
          )}
        </Stack>
      </Modal>

      {/* Block User Modal */}
      <Modal
        opened={blockModal}
        onClose={() => setBlockModal(false)}
        title={`Block User - ${selectedUser?.username || ''}`}
        size="sm"
      >
        <Stack>
          {selectedUser && (
            <>
              <Alert color="red" mb="md">
                <Text size="sm">
                  You are about to block <strong>{selectedUser.username}</strong>.
                  This will prevent them from accessing the system, but their roles will remain intact.
                </Text>
              </Alert>

              <TextInput
                label="Reason for Blocking"
                placeholder="Enter reason (required)"
                value={blockReason}
                onChange={(e) => setBlockReason(e.currentTarget.value)}
                required
                multiline
                rows={3}
              />

              <Group justify="flex-end" mt="md">
                <Button
                  variant="light"
                  onClick={() => setBlockModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  color="red"
                  onClick={handleConfirmBlock}
                  loading={loading}
                  disabled={!blockReason.trim()}
                >
                  Block User
                </Button>
              </Group>
            </>
          )}
        </Stack>
      </Modal>
    </Stack>
  );
}

export default UserManagementPanel;

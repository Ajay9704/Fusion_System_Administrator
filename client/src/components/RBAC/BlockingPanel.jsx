import React, { useState, useEffect } from 'react';
import {
  Stack,
  Group,
  Text,
  TextInput,
  Button,
  Paper,
  Table,
  Badge,
  ActionIcon,
  Loader,
  Alert,
  Title,
  Chip,
} from '@mantine/core';
import {
  IconSearch,
  IconRefresh,
  IconLockOpen,
  IconBan,
} from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';

import { getBlockedUsers, unblockUser } from '../../services/rbacService';

function BlockingPanel({ onRefresh }) {
  const [blockedUsers, setBlockedUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [unblocking, setUnblocking] = useState({});

  useEffect(() => {
    fetchBlockedUsers();
  }, []);

  const fetchBlockedUsers = async () => {
    try {
      setLoading(true);
      const data = await getBlockedUsers();

      if (data.success) {
        setBlockedUsers(data.blocked_users || []);
      } else {
        showNotification({
          title: 'Error',
          message: data.error || 'Failed to fetch blocked users',
          color: 'red',
        });
      }
    } catch (error) {
      console.error('Error fetching blocked users:', error);
      showNotification({
        title: 'Error',
        message: 'Failed to fetch blocked users',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUnblockUser = async (username) => {
    try {
      setUnblocking(prev => ({ ...prev, [username]: true }));

      await unblockUser(username);

      showNotification({
        title: 'Success',
        message: `User '${username}' has been unblocked`,
        color: 'green',
      });

      await fetchBlockedUsers();
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Error unblocking user:', error);
      showNotification({
        title: 'Error',
        message: error.message || 'Failed to unblock user',
        color: 'red',
      });
    } finally {
      setUnblocking(prev => ({ ...prev, [username]: false }));
    }
  };

  // Filter blocked users
  const filteredUsers = blockedUsers.filter(user =>
    user.username?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Stack>
      <Group justify="space-between" mb="md">
        <Title order={3}>Blocked Users</Title>

        <Group>
          <TextInput
            placeholder="Search blocked users..."
            leftSection={<IconSearch size={16} />}
            value={search}
            onChange={(e) => setSearch(e.currentTarget.value)}
            style={{ width: 300 }}
          />
          <Button
            leftSection={<IconRefresh size={16} />}
            onClick={fetchBlockedUsers}
            loading={loading}
          >
            Refresh
          </Button>
        </Group>
      </Group>

      <Alert mb="md">
        <Text size="sm">
          Blocked users cannot login or access the system. Their roles remain intact.
          Unblock to restore access.
        </Text>
      </Alert>

      <Paper shadow="xs" withBorder>
        {loading ? (
          <Stack align="center" p="xl">
            <Loader />
            <Text size="sm" c="dimmed">Loading blocked users...</Text>
          </Stack>
        ) : filteredUsers.length === 0 ? (
          <Text ta="center" c="dimmed" py="xl">
            No blocked users
          </Text>
        ) : (
          <Table.ScrollContainer minWidth={800}>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Username</Table.Th>
                  <Table.Th>Type</Table.Th>
                  <Table.Th>Roles</Table.Th>
                  <Table.Th>Department</Table.Th>
                  <Table.Th style={{ textAlign: 'right' }}>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {filteredUsers.map((user) => (
                  <Table.Tr key={user.username}>
                    <Table.Td>
                      <Badge color="red">{user.username}</Badge>
                    </Table.Td>
                    <Table.Td>
                      <Badge color={user.user_type === 'student' ? 'blue' : user.user_type === 'faculty' ? 'green' : 'orange'}>
                        {user.user_type?.toUpperCase()}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        {user.roles && user.roles.map((role) => (
                          <Chip key={role} size="xs" color="gray">
                            {role}
                          </Chip>
                        ))}
                        {(!user.roles || user.roles.length === 0) && (
                          <Text size="sm" c="dimmed">No roles</Text>
                        )}
                      </Group>
                    </Table.Td>
                    <Table.Td>{user.department || 'N/A'}</Table.Td>
                    <Table.Td ta="right">
                      <Button
                        size="xs"
                        leftSection={<IconLockOpen size={14} />}
                        onClick={() => handleUnblockUser(user.username)}
                        loading={unblocking[user.username]}
                        color="green"
                      >
                        Unblock
                      </Button>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        )}
      </Paper>
    </Stack>
  );
}

export default BlockingPanel;

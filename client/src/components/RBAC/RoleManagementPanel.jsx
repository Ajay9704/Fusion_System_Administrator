import React, { useState, useEffect } from 'react';
import {
  Stack,
  Paper,
  Title,
  Text,
  Table,
  Badge,
  ActionIcon,
  Loader,
  Alert,
  Group,
  Button,
} from '@mantine/core';
import { IconRefresh, IconTrash, IconEdit } from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';

import {
  getAllRoles,
  getRolePermissions,
  updateRolePermissions
} from '../../services/roleService';

function RoleManagementPanel({ onRefresh }) {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchRoles();
  }, []);

  const fetchRoles = async () => {
    try {
      setLoading(true);
      const data = await getAllRoles({ category: null, basic: null });
      setRoles(data || []);
    } catch (error) {
      console.error('Error fetching roles:', error);
      showNotification({
        title: 'Error',
        message: 'Failed to load roles',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Stack>
      <Group justify="space-between" mb="md">
        <Title order={3}>Role Management</Title>
        <Button
          leftSection={<IconRefresh size={16} />}
          onClick={fetchRoles}
          loading={loading}
        >
          Refresh
        </Button>
      </Group>

      <Alert mb="md">
        <Text size="sm">
          View and manage all system roles. Use "Create Custom Role" to add new roles.
        </Text>
      </Alert>

      <Paper shadow="xs" withBorder>
        <Table.ScrollContainer minWidth={800}>
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Role Name</Table.Th>
                <Table.Th>Full Name</Table.Th>
                <Table.Th>Category</Table.Th>
                <Table.Th>Singular</Table.Th>
                <Table.Th style={{ textAlign: 'right' }}>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {loading ? (
                <Table.Tr>
                  <Table.Td colSpan={6}>
                    <Stack align="center" p="xl">
                      <Loader />
                    </Stack>
                  </Table.Td>
                </Table.Tr>
              ) : roles.length === 0 ? (
                <Table.Tr>
                  <Table.Td colSpan={6}>
                    <Text ta="center" c="dimmed" py="xl">
                      No roles found
                    </Text>
                  </Table.Td>
                </Table.Tr>
              ) : (
                roles.map((role) => (
                  <Table.Tr key={role.id}>
                    <Table.Td>
                      <Badge color="blue">{role.name}</Badge>
                    </Table.Td>
                    <Table.Td>{role.full_name}</Table.Td>
                    <Table.Td>
                      <Badge color={role.category === 'faculty' ? 'green' : role.category === 'staff' ? 'orange' : 'gray'}>
                        {role.category?.toUpperCase() || 'N/A'}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      {role.is_singular ? (
                        <Badge color="red" size="xs">SINGULAR</Badge>
                      ) : (
                        <Badge color="gray" size="xs">MULTIPLE</Badge>
                      )}
                    </Table.Td>
                    <Table.Td style={{ textAlign: 'right' }}>
                      <ActionIcon
                        color="blue"
                        variant="light"
                        radius="xs"
                        title="Manage Permissions"
                      >
                        <IconEdit size={18} />
                      </ActionIcon>
                    </Table.Td>
                  </Table.Tr>
                ))
              )}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>
      </Paper>
    </Stack>
  );
}

export default RoleManagementPanel;

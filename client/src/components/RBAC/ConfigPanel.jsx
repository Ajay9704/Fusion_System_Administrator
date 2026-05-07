import React, { useState, useEffect } from 'react';
import {
  Stack,
  Paper,
  Title,
  Text,
  Table,
  Badge,
  Loader,
  Alert,
  Accordion,
  Code,
  Button,
  Group,
  TextInput,
  Modal,
  Select,
  Chip,
} from '@mantine/core';
import { IconInfoCircle, IconEdit, IconRefresh, IconCheck } from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';
import apiClient from '../../services/api';

async function fetchEligibilityRules() {
  const response = await apiClient.get('/rbac/config/eligibility/manage/');
  return response.data;
}

async function updateEligibilityRule(roleName, eligibleTypes) {
  const response = await apiClient.post('/rbac/config/eligibility/manage/', {
    role_name: roleName,
    eligible_user_types: eligibleTypes,
  });
  return response.data;
}

async function fetchConflictRules() {
  const response = await apiClient.get('/rbac/config/conflicts/manage/');
  return response.data;
}

async function updateConflictRule(roleName, conflicts) {
  const response = await apiClient.post('/rbac/config/conflicts/manage/', {
    role_name: roleName,
    conflicts_with: conflicts,
  });
  return response.data;
}

function ConfigPanel() {
  const [eligibility, setEligibility] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editModal, setEditModal] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [editType, setEditType] = useState(null);
  const [editValue, setEditValue] = useState([]);

  useEffect(() => {
    fetchConfiguration();
  }, []);

  const fetchConfiguration = async () => {
    try {
      setLoading(true);

      const [eligibilityData, conflictsData] = await Promise.all([
        fetchEligibilityRules(),
        fetchConflictRules(),
      ]);

      setEligibility(eligibilityData.rules || []);
      setConflicts(conflictsData.rules || []);
    } catch (error) {
      console.error('Error fetching configuration:', error);
      showNotification({
        title: 'Error',
        message: 'Failed to load RBAC configuration',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const openEditModal = (rule, type) => {
    setEditingRule(rule);
    setEditType(type);
    setEditValue(type === 'eligibility' ? rule.eligible_user_types : rule.conflicts_with);
    setEditModal(true);
  };

  const handleSaveEdit = async () => {
    try {
      setLoading(true);

      if (editType === 'eligibility') {
        await updateEligibilityRule(editingRule.role_name, editValue);
        showNotification({ title: 'Success', message: 'Eligibility rule updated', color: 'green' });
      } else {
        await updateConflictRule(editingRule.role_name, editValue);
        showNotification({ title: 'Success', message: 'Conflict rule updated', color: 'green' });
      }

      await fetchConfiguration();
      setEditModal(false);
    } catch (error) {
      showNotification({ title: 'Error', message: 'Failed to update rule', color: 'red' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={3}>RBAC Configuration</Title>
        <Button leftSection={<IconRefresh size={16} />} onClick={fetchConfiguration} loading={loading}>
          Refresh
        </Button>
      </Group>

      <Alert icon={<IconInfoCircle />}>
        <Text size="sm">
          Edit role eligibility and conflict rules in real-time. Changes are stored in the database and enforced immediately.
        </Text>
      </Alert>

      {loading && eligibility.length === 0 ? (
        <Stack align="center" p="xl">
          <Loader />
        </Stack>
      ) : (
        <Stack>
          {/* Eligibility Rules */}
          <Paper shadow="xs" p="md" withBorder>
            <Group justify="space-between" mb="sm">
              <Title order={5}>Role Eligibility Rules ({eligibility.length})</Title>
            </Group>

            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Role</Table.Th>
                  <Table.Th>Eligible User Types</Table.Th>
                  <Table.Th style={{ textAlign: 'right' }}>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {eligibility.map((rule) => (
                  <Table.Tr key={rule.id}>
                    <Table.Td>
                      <Badge color="blue">{rule.role_name}</Badge>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        {rule.eligible_user_types.map((type) => (
                          <Badge key={type} color="green" variant="light">
                            {type}
                          </Badge>
                        ))}
                      </Group>
                    </Table.Td>
                    <Table.Td style={{ textAlign: 'right' }}>
                      <Button
                        size="xs"
                        leftSection={<IconEdit size={14} />}
                        onClick={() => openEditModal(rule, 'eligibility')}
                        variant="light"
                      >
                        Edit
                      </Button>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Paper>

          {/* Conflict Rules */}
          <Paper shadow="xs" p="md" withBorder>
            <Group justify="space-between" mb="sm">
              <Title order={5}>Role Conflict Rules ({conflicts.length})</Title>
            </Group>

            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Role</Table.Th>
                  <Table.Th>Conflicts With</Table.Th>
                  <Table.Th style={{ textAlign: 'right' }}>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {conflicts.map((rule) => (
                  <Table.Tr key={rule.id}>
                    <Table.Td>
                      <Badge color="blue">{rule.role_name}</Badge>
                    </Table.Td>
                    <Table.Td>
                      {rule.conflicts_with.length > 0 ? (
                        <Group gap="xs">
                          {rule.conflicts_with.map((conflict) => (
                            <Badge key={conflict} color="red" variant="light">
                              {conflict}
                            </Badge>
                          ))}
                        </Group>
                      ) : (
                        <Text size="sm" c="dimmed">No conflicts</Text>
                      )}
                    </Table.Td>
                    <Table.Td style={{ textAlign: 'right' }}>
                      <Button
                        size="xs"
                        leftSection={<IconEdit size={14} />}
                        onClick={() => openEditModal(rule, 'conflicts')}
                        variant="light"
                      >
                        Edit
                      </Button>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Paper>
        </Stack>
      )}

      {/* Edit Modal */}
      <Modal opened={editModal} onClose={() => setEditModal(false)} title={`Edit ${editingRule?.role_name}`} size="md">
        <Stack>
          <Text size="sm" c="dimmed">
            {editType === 'eligibility' ? 'Edit eligible user types (comma separated)' : 'Edit conflicting roles (comma separated)'}
          </Text>
          <TextInput
            label="Values"
            placeholder="student, faculty, staff"
            value={editValue.join(', ')}
            onChange={(e) => setEditValue(e.target.value.split(', ').filter(Boolean))}
          />
          <Group justify="flex-end">
            <Button variant="light" onClick={() => setEditModal(false)}>Cancel</Button>
            <Button leftSection={<IconCheck size={16} />} onClick={handleSaveEdit} loading={loading}>
              Save Changes
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}

export default ConfigPanel;

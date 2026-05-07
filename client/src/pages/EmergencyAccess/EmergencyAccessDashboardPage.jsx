import React, { useState, useEffect } from 'react';
import {
  Container,
  Title,
  Paper,
  Tabs,
  Text,
  TextInput,
  Textarea,
  NumberInput,
  Button,
  Select,
  Stack,
  Grid,
  Card,
  Badge,
  Alert,
  Loader,
  Table,
  ActionIcon,
  Modal,
  Group,
  Progress,
  ThemeIcon,
  Center,
} from '@mantine/core';
import {
  IconShield,
  IconClock,
  IconCheck,
  IconX,
  IconHistory,
  IconAlertCircle,
  IconRefresh,
  IconKey,
} from '@tabler/icons-react';
import { showNotification, updateNotification } from '@mantine/notifications';
import { useMediaQuery } from '@mantine/hooks';
import api from '../../services/api';
import {
  getMyEmergencyRequests,
  getMyActiveTemporaryRoles,
  createEmergencyRequest,
} from '../../services/emergencyAccessService';

function EmergencyAccessDashboardPage() {
  const isSmallScreen = useMediaQuery('(max-width: 768px)');
  const [activeTab, setActiveTab] = useState('my-requests');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // My requests data
  const [myRequests, setMyRequests] = useState([]);
  const [activeTemporaryRoles, setActiveTemporaryRoles] = useState([]);

  // Request form
  const [requestForm, setRequestForm] = useState({
    role_id: '',
    duration: 60,
    reason: '',
  });
  const [availableRoles, setAvailableRoles] = useState([]);
  const [formErrors, setFormErrors] = useState({});

  // Refresh data
  const fetchData = async () => {
    try {
      setLoading(true);
      const [requestsData, rolesData] = await Promise.all([
        getMyEmergencyRequests(),
        getMyActiveTemporaryRoles(),
      ]);
      setMyRequests(requestsData);
      setActiveTemporaryRoles(rolesData);
    } catch (error) {
      showNotification({
        title: 'Error',
        message: error.message || 'Failed to fetch data',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  // Fetch available roles
  const fetchAvailableRoles = async () => {
    try {
      const response = await api.get('/view-roles');
      setAvailableRoles(response.data.filter(role => !role.basic));
    } catch (error) {
      console.error('Error fetching roles:', error);
    }
  };

  useEffect(() => {
    fetchData();
    fetchAvailableRoles();

    // Auto-refresh every 30 seconds for real-time updates
    const interval = setInterval(() => {
      fetchData();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
    showNotification({
      title: 'Refreshed',
      message: 'Data updated successfully',
      color: 'green',
    });
  };

  const handleCreateRequest = async () => {
    // Validation
    const errors = {};
    if (!requestForm.role_id) errors.role_id = 'Role is required';
    if (!requestForm.duration || requestForm.duration < 1) errors.duration = 'Duration must be at least 1 minute';
    if (!requestForm.reason || requestForm.reason.length < 10) errors.reason = 'Reason must be at least 10 characters';

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    try {
      setLoading(true);
      await createEmergencyRequest(
        parseInt(requestForm.role_id),
        parseInt(requestForm.duration),
        requestForm.reason
      );

      showNotification({
        title: 'Success',
        message: 'Emergency access request created successfully',
        color: 'green',
      });

      // Reset form
      setRequestForm({
        role_id: '',
        duration: 60,
        reason: '',
      });
      setFormErrors({});

      // Refresh data
      await fetchData();
    } catch (error) {
      showNotification({
        title: 'Error',
        message: error.message || 'Failed to create request',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      PENDING: { color: 'yellow', label: 'Pending' },
      APPROVED: { color: 'green', label: 'Approved' },
      REJECTED: { color: 'red', label: 'Rejected' },
      EXPIRED: { color: 'gray', label: 'Expired' },
      WITHDRAWN: { color: 'orange', label: 'Withdrawn' },
    };
    const config = statusConfig[status] || { color: 'gray', label: status };
    return <Badge color={config.color}>{config.label}</Badge>;
  };

  const formatDuration = (minutes) => {
    if (minutes < 60) return `${minutes} minutes`;
    if (minutes < 1440) return `${Math.round(minutes / 60)} hours`;
    return `${Math.round(minutes / 1440)} days`;
  };

  const getTimeRemaining = (expiresAt) => {
    if (!expiresAt) return 'N/A';
    const now = new Date();
    const expires = new Date(expiresAt);
    const diff = expires - now;

    if (diff <= 0) return 'Expired';

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  // My Requests Panel
  const MyRequestsPanel = () => (
    <Stack spacing="md">
      <Group position="apart">
        <Text size="lg" weight={500}>My Emergency Access Requests</Text>
        <ActionIcon
          color="blue"
          onClick={handleRefresh}
          loading={refreshing}
        >
          <IconRefresh size={16} />
        </ActionIcon>
      </Group>

      {loading ? (
        <Center>
          <Loader size="md" />
        </Center>
      ) : myRequests.length === 0 ? (
        <Alert icon={<IconAlertCircle size={16} />} color="blue">
          No emergency access requests found. Create your first request!
        </Alert>
      ) : (
        <Table striped highlightOnHover>
          <thead>
            <tr>
              <th>Role</th>
              <th>Reason</th>
              <th>Duration</th>
              <th>Status</th>
              <th>Created</th>
              <th>Expires</th>
            </tr>
          </thead>
          <tbody>
            {myRequests.map((request) => (
              <tr key={request.id}>
                <td>{request.role}</td>
                <td style={{ maxWidth: '200px' }}>
                  <Text lineClamp={2} size="sm">
                    {request.reason}
                  </Text>
                </td>
                <td>
                  {request.approved_duration
                    ? formatDuration(request.approved_duration)
                    : formatDuration(request.requested_duration)}
                  {request.approved_duration !== request.requested_duration && (
                    <Badge size="xs" ml="xs" color="orange">Modified</Badge>
                  )}
                </td>
                <td>{getStatusBadge(request.status)}</td>
                <td>{new Date(request.requested_at).toLocaleString()}</td>
                <td>
                  {request.expires_at ? (
                    <Group spacing={4}>
                      <Text size="sm">{getTimeRemaining(request.expires_at)}</Text>
                      {request.is_active && (
                        <Badge size="xs" color="green">Active</Badge>
                      )}
                    </Group>
                  ) : (
                    'N/A'
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </Stack>
  );

  // Active Temporary Roles Panel
  const ActiveRolesPanel = () => (
    <Stack spacing="md">
      <Group position="apart">
        <Text size="lg" weight={500}>My Active Temporary Roles</Text>
        <ActionIcon
          color="blue"
          onClick={handleRefresh}
          loading={refreshing}
        >
          <IconRefresh size={16} />
        </ActionIcon>
      </Group>

      {loading ? (
        <Center>
          <Loader size="md" />
        </Center>
      ) : activeTemporaryRoles.length === 0 ? (
        <Alert icon={<IconAlertCircle size={16} />} color="blue">
          No active temporary roles. Your approved emergency access will appear here.
        </Alert>
      ) : (
        <Stack spacing="sm">
          {activeTemporaryRoles.map((role) => (
            <Card key={role.id} shadow="sm" p="md" withBorder>
              <Group position="apart" mb="xs">
                <Text weight={500}>{role.role_full_name || role.role_name}</Text>
                <Badge color="green">Active</Badge>
              </Group>
              <Stack spacing="xs">
                <Group spacing={4}>
                  <IconClock size={14} />
                  <Text size="sm">
                    Expires in: {getTimeRemaining(role.expires_at)}
                  </Text>
                </Group>
                <Text size="xs" color="dimmed">
                  Granted: {new Date(role.granted_at).toLocaleString()}
                </Text>
                {role.expires_at && (
                  <Progress
                    value={Math.max(0, Math.min(100,
                      ((new Date(role.expires_at) - new Date()) /
                        (new Date(role.expires_at) - new Date(role.granted_at))) * 100
                    ))}
                    size="sm"
                    color={getTimeRemaining(role.expires_at) === 'Expired' ? 'red' : 'blue'}
                  />
                )}
              </Stack>
            </Card>
          ))}
        </Stack>
      )}
    </Stack>
  );

  // Create Request Panel
  const CreateRequestPanel = () => (
    <Stack spacing="md">
      <Text size="lg" weight={500}>Request Emergency Access</Text>

      <Alert icon={<IconAlertCircle size={16} />} color="blue">
        Emergency access provides temporary elevated role access. All requests require admin approval.
      </Alert>

      <Stack spacing="sm">
        <Select
          label="Role"
          placeholder="Select a role to request"
          data={availableRoles.map((role) => ({
            value: role.id.toString(),
            label: role.full_name || role.name,
          }))}
          value={requestForm.role_id}
          onChange={(value) => setRequestForm({ ...requestForm, role_id: value })}
          error={formErrors.role_id}
          required
        />

        <NumberInput
          label="Duration (minutes)"
          description="Maximum 24 hours (1440 minutes)"
          min={1}
          max={1440}
          value={requestForm.duration}
          onChange={(value) => setRequestForm({ ...requestForm, duration: value })}
          error={formErrors.duration}
          required
        />

        <Textarea
          label="Reason"
          placeholder="Please provide a detailed reason for requesting emergency access (minimum 10 characters)"
          minRows={4}
          value={requestForm.reason}
          onChange={(event) => setRequestForm({ ...requestForm, reason: event.currentTarget.value })}
          error={formErrors.reason}
          required
        />

        <Button
          onClick={handleCreateRequest}
          loading={loading}
          fullWidth
          size="md"
        >
          Submit Request
        </Button>
      </Stack>
    </Stack>
  );

  return (
    <Container size="xl" py="md">
      <Stack spacing="lg">
        {/* Header */}
        <Paper shadow="xs" p="md" withBorder>
          <Group position="apart">
            <Group spacing="sm">
              <ThemeIcon color="blue" size="lg">
                <IconShield size={24} />
              </ThemeIcon>
              <div>
                <Title order={3}>Emergency Access</Title>
                <Text size="sm" color="dimmed">
                  Request temporary elevated role access
                </Text>
              </div>
            </Group>
            <Badge size="lg" color="blue">
              <IconKey size={14} style={{ marginRight: 4 }} />
              Just-In-Time Access
            </Badge>
          </Group>
        </Paper>

        {/* Tabs */}
        <Tabs value={activeTab} onTabChange={setActiveTab}>
          <Tabs.List>
            <Tabs.Tab value="my-requests" icon={<IconHistory size={16} />}>
              My Requests ({myRequests.length})
            </Tabs.Tab>
            <Tabs.Tab value="active-roles" icon={<IconCheck size={16} />}>
              Active Roles ({activeTemporaryRoles.length})
            </Tabs.Tab>
            <Tabs.Tab value="create-request" icon={<IconShield size={16} />}>
              New Request
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="my-requests" pt="md">
            <Paper shadow="xs" p="md" withBorder>
              <MyRequestsPanel />
            </Paper>
          </Tabs.Panel>

          <Tabs.Panel value="active-roles" pt="md">
            <Paper shadow="xs" p="md" withBorder>
              <ActiveRolesPanel />
            </Paper>
          </Tabs.Panel>

          <Tabs.Panel value="create-request" pt="md">
            <Paper shadow="xs" p="md" withBorder>
              <CreateRequestPanel />
            </Paper>
          </Tabs.Panel>
        </Tabs>
      </Stack>
    </Container>
  );
}

export default EmergencyAccessDashboardPage;

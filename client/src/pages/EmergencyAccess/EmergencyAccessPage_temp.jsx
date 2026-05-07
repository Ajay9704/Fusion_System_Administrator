import React, { useState, useEffect } from 'react';
import {
  Container,
  Title,
  Paper,
  Text,
  Textarea,
  NumberInput,
  Button,
  Select,
  Stack,
  Card,
  Badge,
  Alert,
  Loader,
  Table,
  ActionIcon,
  Modal,
  Group,
  Grid,
} from '@mantine/core';
import {
  IconShield,
  IconClock,
  IconCheck,
  IconX,
  IconAlertCircle,
  IconRefresh,
  IconKey,
  IconUser,
  IconEye,
} from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';
import api from '../../services/api';
import {
  getMyEmergencyRequests,
  getPendingEmergencyRequests,
  getAllEmergencyRequests,
  getMyActiveTemporaryRoles,
  createEmergencyRequest,
  approveEmergencyRequest,
  rejectEmergencyRequest,
  getEmergencyRequestDetail,
} from '../../services/emergencyAccessService';

function EmergencyAccessPage() {
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Data
  const [myRequests, setMyRequests] = useState([]);
  const [pendingRequests, setPendingRequests] = useState([]);
  const [allRequests, setAllRequests] = useState([]);
  const [activeRoles, setActiveRoles] = useState([]);
  const [availableRoles, setAvailableRoles] = useState([]);

  // Request form
  const [requestForm, setRequestForm] = useState({
    role_id: '',
    duration: 60,
    reason: '',
  });
  const [formErrors, setFormErrors] = useState({});

  // Modals
  const [approveModal, setApproveModal] = useState({ open: false, request: null });
  const [rejectModal, setRejectModal] = useState({ open: false, request: null });
  const [detailModal, setDetailModal] = useState({ open: false, request: null });

  // Form data
  const [approveForm, setApproveForm] = useState({
    approved_duration: null,
    duration_modified_reason: '',
  });
  const [rejectForm, setRejectForm] = useState({ rejection_reason: '' });

  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');

  // Fetch all data
  const fetchData = async () => {
    try {
      setLoading(true);
      const [myData, pendingData, allData, activeData] = await Promise.all([
        getMyEmergencyRequests(),
        getPendingEmergencyRequests(),
        getAllEmergencyRequests(100),
        getMyActiveTemporaryRoles(),
      ]);
      setMyRequests(myData);
      setPendingRequests(pendingData);
      setAllRequests(allData);
      setActiveRoles(activeData);

      console.log('Data fetched successfully:', {
        myRequests: myData.length,
        pendingRequests: pendingData.length,
        allRequests: allData.length,
        activeRoles: activeData.length
      });
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

  // Initial data fetch and auto-refresh
  useEffect(() => {
    fetchData();
    fetchAvailableRoles();

    // Auto-refresh every 10 seconds for near real-time updates
    const interval = setInterval(fetchData, 10000);

    return () => clearInterval(interval);
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
    showNotification({
      title: 'Refreshed',
      message: 'Data updated',
      color: 'green',
      autoClose: 1500,
    });
  };

  const handleCreateRequest = async () => {
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
        message: 'Emergency access request created',
        color: 'green',
      });

      setRequestForm({ role_id: '', duration: 60, reason: '' });
      setFormErrors({});
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

  const handleApprove = async () => {
    try {
      setLoading(true);
      await approveEmergencyRequest(
        approveModal.request.id,
        approveForm.approved_duration ? parseInt(approveForm.approved_duration) : null,
        approveForm.duration_modified_reason || null
      );

      showNotification({
        title: 'Success',
        message: 'Request approved',
        color: 'green',
      });

      setApproveModal({ open: false, request: null });
      setApproveForm({ approved_duration: null, duration_modified_reason: '' });
      await fetchData();
    } catch (error) {
      showNotification({
        title: 'Error',
        message: error.message || 'Failed to approve',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    try {
      setLoading(true);
      await rejectEmergencyRequest(
        rejectModal.request.id,
        rejectForm.rejection_reason || null
      );

      showNotification({
        title: 'Success',
        message: 'Request rejected',
        color: 'green',
      });

      setRejectModal({ open: false, request: null });
      setRejectForm({ rejection_reason: '' });
      await fetchData();
    } catch (error) {
      showNotification({
        title: 'Error',
        message: error.message || 'Failed to reject',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (requestId) => {
    try {
      const details = await getEmergencyRequestDetail(requestId);
      setDetailModal({ open: true, request: details });
    } catch (error) {
      showNotification({
        title: 'Error',
        message: 'Failed to fetch request details',
        color: 'red',
      });
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
    if (!minutes) return 'N/A';
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

  return (
    <>
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
                  Just-In-Time role access management
                </Text>
              </div>
            </Group>
            <Group spacing="sm">
              <Badge size="lg" color="blue">
                <IconKey size={14} style={{ marginRight: 4 }} />
                Active: {activeRoles.length}
              </Badge>
              <Badge size="lg" color="yellow">
                Pending: {pendingRequests.length}
              </Badge>
              <ActionIcon color="blue" onClick={handleRefresh} loading={refreshing}>
                <IconRefresh size={20} />
              </ActionIcon>
            </Group>
          </Group>
        </Paper>

        {/* Request Form */}
        <Paper shadow="xs" p="md" withBorder>
          <Title order={4} mb="md">Request Emergency Access</Title>
          <Grid>
            <Grid.Col span={4}>
              <Select
                label="Role"
                placeholder="Select role"
                data={availableRoles.map(r => ({ value: r.id.toString(), label: r.full_name || r.name }))}
                value={requestForm.role_id}
                onChange={(v) => setRequestForm({ ...requestForm, role_id: v })}
                error={formErrors.role_id}
                required
              />
            </Grid.Col>
            <Grid.Col span={3}>
              <NumberInput
                label="Duration (minutes)"
                description="Max 24 hours"
                min={1}
                max={1440}
                value={requestForm.duration}
                onChange={(v) => setRequestForm({ ...requestForm, duration: v })}
                error={formErrors.duration}
                required
              />
            </Grid.Col>
            <Grid.Col span={5}>
              <Textarea
                label="Reason"
                placeholder="Minimum 10 characters - detailed justification required"
                minRows={1}
                value={requestForm.reason}
                onChange={(e) => setRequestForm({ ...requestForm, reason: e.currentTarget.value })}
                error={formErrors.reason}
                required
              />
            </Grid.Col>
            <Grid.Col span={1}>
              <Button onClick={handleCreateRequest} loading={loading} fullWidth mt="lg">
                Submit
              </Button>
            </Grid.Col>
          </Grid>
        </Paper>

        {/* Active Temporary Roles */}
        {activeRoles.length > 0 && (
          <Paper shadow="xs" p="md" withBorder>
            <Title order={4} mb="md">Active Temporary Roles ({activeRoles.length})</Title>
            <Grid>
              {activeRoles.map(role => (
                <Grid.Col span={4} key={role.id}>
                  <Card shadow="sm" p="sm" withBorder>
                    <Group position="apart" mb="xs">
                      <Text weight={500}>{role.role_full_name || role.role_name}</Text>
                      <Badge color="green">Active</Badge>
                    </Group>
                    <Group spacing={4}>
                      <IconClock size={14} />
                      <Text size="sm">{getTimeRemaining(role.expires_at)}</Text>
                    </Group>
                  </Card>
                </Grid.Col>
              ))}
            </Grid>
          </Paper>
        )}

        {/* My Requests */}
        <Paper shadow="xs" p="md" withBorder>
          <Title order={4} mb="md">My Requests ({myRequests.length})</Title>
          {loading ? <Loader /> : myRequests.length === 0 ? (
            <Alert icon={<IconAlertCircle size={16} />} color="blue">No requests yet</Alert>
          ) : (
            <Table striped>
              <thead>
                <tr>
                  <th>Role</th>
                  <th>Duration</th>
                  <th>Status</th>
                  <th>Expires</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {myRequests.map(req => (
                  <tr key={req.id}>
                    <td>{req.role}</td>
                    <td>{formatDuration(req.approved_duration || req.requested_duration)}</td>
                    <td>{getStatusBadge(req.status)}</td>
                    <td>{req.expires_at ? getTimeRemaining(req.expires_at) : 'N/A'}</td>
                    <td>
                      <ActionIcon color="blue" onClick={() => handleViewDetails(req.id)}>
                        <IconEye size={16} />
                      </ActionIcon>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Paper>

        {/* Pending Requests */}
        {pendingRequests.length > 0 && (
          <Paper shadow="xs" p="md" withBorder>
            <Title order={4} mb="md">Pending Requests ({pendingRequests.length})</Title>
            <Stack spacing="sm">
              {pendingRequests.map(req => (
                <Card key={req.id} shadow="sm" p="md" withBorder>
                  <Group position="apart" mb="xs">
                    <Group spacing="sm">
                      <ThemeIcon color="blue" size="sm">
                        <IconUser size={16} />
                      </ThemeIcon>
                      <Text weight={500}>{req.user}</Text>
                    </Group>
                    <Badge color="yellow">Pending</Badge>
                  </Group>
                  <Group spacing="xl">
                    <div>
                      <Text size="xs" color="dimmed">Role</Text>
                      <Text size="sm">{req.role}</Text>
                    </div>
                    <div>
                      <Text size="xs" color="dimmed">Duration</Text>
                      <Text size="sm">{formatDuration(req.requested_duration)}</Text>
                    </div>
                  </Group>
                  <Text size="sm" mt="xs">{req.reason}</Text>
                  <Group spacing="sm" mt="sm">
                    {req.user !== currentUser.username ? (
                      <>
                        <Button size="sm" color="green" onClick={() => {
                          setApproveModal({ open: true, request: req });
                          setApproveForm({ approved_duration: req.requested_duration, duration_modified_reason: '' });
                        }}>
                          Approve
                        </Button>
                        <Button size="sm" color="red" onClick={() => {
                          setRejectModal({ open: true, request: req });
                          setRejectForm({ rejection_reason: '' });
                        }}>
                          Reject
                        </Button>
                      </>
                    ) : (
                      <Badge color="gray">Cannot approve own</Badge>
                    )}
                    <ActionIcon color="blue" onClick={() => handleViewDetails(req.id)}>
                      <IconEye size={16} />
                    </ActionIcon>
                  </Group>
                </Card>
              ))}
            </Stack>
          </Paper>
        )}

        {/* All History with Details */}
        <Paper shadow="xs" p="md" withBorder>
          <Group position="apart" mb="md">
            <Title order={4}>All History ({allRequests.length})</Title>
            <Badge color="blue">Full Audit Trail</Badge>
          </Group>
          {loading ? <Loader /> : (
            <Table striped highlightOnHover>
              <thead>
                <tr>
                  <th>Actions</th>
                  <th>Requester</th>
                  <th>Role</th>
                  <th>Requested</th>
                  <th>Granted</th>
                  <th>Status</th>
                  <th>Reviewer</th>
                  <th>Expires</th>
                </tr>
              </thead>
              <tbody>
                {allRequests.map(req => (
                  <tr key={req.id}>
                    <td>
                      <ActionIcon color="blue" onClick={() => handleViewDetails(req.id)}>
                        <IconEye size={16} />
                      </ActionIcon>
                    </td>
                    <td>{req.user}</td>
                    <td>{req.role}</td>
                    <td>{formatDuration(req.requested_duration)}</td>
                    <td>{req.approved_duration ? formatDuration(req.approved_duration) : 'N/A'}</td>
                    <td>{getStatusBadge(req.status)}</td>
                    <td>{req.reviewed_by || 'N/A'}</td>
                    <td>{req.expires_at ? new Date(req.expires_at).toLocaleString() : 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Paper>
      </Stack>
    </Container>

    {/* Modals */}
    <Modal opened={approveModal.open} onClose={() => setApproveModal({ open: false, request: null })} title="Approve Emergency Access Request">
        <Stack spacing="md">
          {approveModal.request && (
            <>
              <Alert icon={<IconAlertCircle size={16} />} color="blue">
                <Text><strong>Requester:</strong> {approveModal.request.user}</Text>
                <Text><strong>Role:</strong> {approveModal.request.role}</Text>
                <Text><strong>Requested Duration:</strong> {formatDuration(approveModal.request.requested_duration)}</Text>
              </Alert>
              <NumberInput
                label="Approved Duration (minutes)"
                description="Modify duration if needed (max 1440 minutes = 24 hours)"
                min={1}
                max={1440}
                value={approveForm.approved_duration}
                onChange={(v) => setApproveForm({ ...approveForm, approved_duration: v })}
              />
              <Textarea
                label="Reason for Modification (optional)"
                placeholder="Explain why you're modifying the duration"
                minRows={2}
                value={approveForm.duration_modified_reason}
                onChange={(e) => setApproveForm({ ...approveForm, duration_modified_reason: e.currentTarget.value })}
              />
              <Group position="apart">
                <Button variant="default" onClick={() => setApproveModal({ open: false, request: null })}>
                  Cancel
                </Button>
                <Button color="green" onClick={handleApprove} loading={loading}>
                  Approve
                </Button>
              </Group>
            </>
          )}
        </Stack>
      </Modal>

    <Modal opened={rejectModal.open} onClose={() => setRejectModal({ open: false, request: null })} title="Reject Emergency Access Request">
      <Stack spacing="md">
        {rejectModal.request && (
          <>
            <Alert icon={<IconAlertCircle size={16} />} color="red">
              <Text><strong>Requester:</strong> {rejectModal.request.user}</Text>
              <Text><strong>Role:</strong> {rejectModal.request.role}</Text>
              <Text><strong>Reason:</strong> {rejectModal.request.reason}</Text>
            </Alert>
            <Textarea
              label="Rejection Reason (optional)"
              placeholder="Provide reason for rejection"
              minRows={3}
              value={rejectForm.rejection_reason}
              onChange={(e) => setRejectForm({ ...rejectForm, rejection_reason: e.currentTarget.value })}
            />
            <Group position="apart">
              <Button variant="default" onClick={() => setRejectModal({ open: false, request: null })}>
                Cancel
              </Button>
              <Button color="red" onClick={handleReject} loading={loading}>
                Reject
              </Button>
            </Group>
          </>
        )}
      </Stack>
    </Modal>

    <Modal opened={detailModal.open} onClose={() => setDetailModal({ open: false, request: null })} title="Emergency Access Request Details" size="lg">

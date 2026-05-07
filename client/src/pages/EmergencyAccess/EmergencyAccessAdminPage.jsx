import React, { useState, useEffect } from 'react';
import {
  Container,
  Title,
  Paper,
  Tabs,
  Text,
  Button,
  Stack,
  Table,
  Badge,
  Alert,
  Loader,
  ActionIcon,
  Modal,
  TextInput,
  NumberInput,
  Textarea,
  Group,
  Card,
  Grid,
  ThemeIcon,
  Progress,
} from '@mantine/core';
import {
  IconShield,
  IconClock,
  IconCheck,
  IconX,
  IconRefresh,
  IconKey,
  IconUser,
  IconAlertCircle,
  IconHistory,
  IconEye,
} from '@tabler/icons-react';
import { showNotification, updateNotification } from '@mantine/notifications';
import { useMediaQuery } from '@mantine/hooks';
import {
  getPendingEmergencyRequests,
  getAllEmergencyRequests,
  approveEmergencyRequest,
  rejectEmergencyRequest,
  withdrawEmergencyRequest,
} from '../../services/emergencyAccessService';

function EmergencyAccessAdminPage() {
  const isSmallScreen = useMediaQuery('(max-width: 768px)');
  const [activeTab, setActiveTab] = useState('pending');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Data
  const [pendingRequests, setPendingRequests] = useState([]);
  const [allRequests, setAllRequests] = useState([]);
  const [stats, setStats] = useState({
    pending: 0,
    approved: 0,
    rejected: 0,
    active: 0,
  });

  // Modals
  const [approveModal, setApproveModal] = useState({ open: false, request: null });
  const [rejectModal, setRejectModal] = useState({ open: false, request: null });
  const [withdrawModal, setWithdrawModal] = useState({ open: false, request: null });
  const [detailModal, setDetailModal] = useState({ open: false, request: null });

  // Form data
  const [approveForm, setApproveForm] = useState({
    approved_duration: null,
    duration_modified_reason: '',
  });
  const [rejectForm, setRejectForm] = useState({
    rejection_reason: '',
  });
  const [withdrawForm, setWithdrawForm] = useState({
    revocation_reason: '',
  });

  // Fetch data
  const fetchData = async () => {
    try {
      setLoading(true);
      const [pendingData, allData] = await Promise.all([
        getPendingEmergencyRequests(),
        getAllEmergencyRequests(500),
      ]);

      setPendingRequests(pendingData);
      setAllRequests(allData);

      // Calculate stats
      const stats = {
        pending: pendingData.length,
        approved: allData.filter(r => r.status === 'APPROVED').length,
        rejected: allData.filter(r => r.status === 'REJECTED').length,
        active: allData.filter(r => r.status === 'APPROVED' && r.expires_at && new Date(r.expires_at) > new Date()).length,
      };
      setStats(stats);
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

  useEffect(() => {
    fetchData();

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
        message: 'Emergency access request approved',
        color: 'green',
      });

      setApproveModal({ open: false, request: null });
      setApproveForm({ approved_duration: null, duration_modified_reason: '' });
      await fetchData();
    } catch (error) {
      showNotification({
        title: 'Error',
        message: error.message || 'Failed to approve request',
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
        message: 'Emergency access request rejected',
        color: 'green',
      });

      setRejectModal({ open: false, request: null });
      setRejectForm({ rejection_reason: '' });
      await fetchData();
    } catch (error) {
      showNotification({
        title: 'Error',
        message: error.message || 'Failed to reject request',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleWithdraw = async () => {
    try {
      setLoading(true);
      await withdrawEmergencyRequest(
        withdrawModal.request.id,
        withdrawForm.revocation_reason || null
      );

      showNotification({
        title: 'Success',
        message: 'Emergency access withdrawn successfully',
        color: 'green',
      });

      setWithdrawModal({ open: false, request: null });
      setWithdrawForm({ revocation_reason: '' });
      await fetchData();
    } catch (error) {
      showNotification({
        title: 'Error',
        message: error.message || 'Failed to withdraw request',
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

  // Stats Cards
  const StatsPanel = () => (
    <Grid>
      <Grid.Col span={isSmallScreen ? 6 : 3}>
        <Card shadow="sm" p="md" withBorder>
          <Stack spacing={0}>
            <Text size="sm" color="dimmed">Pending</Text>
            <Text size="xl" weight={500} color="yellow">
              {stats.pending}
            </Text>
          </Stack>
        </Card>
      </Grid.Col>
      <Grid.Col span={isSmallScreen ? 6 : 3}>
        <Card shadow="sm" p="md" withBorder>
          <Stack spacing={0}>
            <Text size="sm" color="dimmed">Active</Text>
            <Text size="xl" weight={500} color="green">
              {stats.active}
            </Text>
          </Stack>
        </Card>
      </Grid.Col>
      <Grid.Col span={isSmallScreen ? 6 : 3}>
        <Card shadow="sm" p="md" withBorder>
          <Stack spacing={0}>
            <Text size="sm" color="dimmed">Approved</Text>
            <Text size="xl" weight={500} color="blue">
              {stats.approved}
            </Text>
          </Stack>
        </Card>
      </Grid.Col>
      <Grid.Col span={isSmallScreen ? 6 : 3}>
        <Card shadow="sm" p="md" withBorder>
          <Stack spacing={0}>
            <Text size="sm" color="dimmed">Rejected</Text>
            <Text size="xl" weight={500} color="red">
              {stats.rejected}
            </Text>
          </Stack>
        </Card>
      </Grid.Col>
    </Grid>
  );

  // Pending Requests Panel
  const PendingRequestsPanel = () => (
    <Stack spacing="md">
      <Group position="apart">
        <Text size="lg" weight={500}>Pending Requests</Text>
        <ActionIcon
          color="blue"
          onClick={handleRefresh}
          loading={refreshing}
        >
          <IconRefresh size={16} />
        </ActionIcon>
      </Group>

      {loading ? (
        <Loader />
      ) : pendingRequests.length === 0 ? (
        <Alert icon={<IconCheck size={16} />} color="green">
          No pending requests!
        </Alert>
      ) : (
        <Stack spacing="sm">
          {pendingRequests.map((request) => (
            <Card key={request.id} shadow="sm" p="md" withBorder>
              <Stack spacing="sm">
                <Group position="apart">
                  <Group spacing="sm">
                    <ThemeIcon color="blue" size="sm">
                      <IconUser size={16} />
                    </ThemeIcon>
                    <Text weight={500}>{request.user}</Text>
                    <Text size="sm" color="dimmed">({request.user_email})</Text>
                  </Group>
                  <Badge color="yellow">Pending</Badge>
                </Group>

                <Group spacing="xl">
                  <div>
                    <Text size="xs" color="dimmed">Role</Text>
                    <Text size="sm">{request.role}</Text>
                  </div>
                  <div>
                    <Text size="xs" color="dimmed">Duration</Text>
                    <Text size="sm">{formatDuration(request.requested_duration)}</Text>
                  </div>
                  <div>
                    <Text size="xs" color="dimmed">Requested</Text>
                    <Text size="sm">{new Date(request.requested_at).toLocaleString()}</Text>
                  </div>
                </Group>

                <div>
                  <Text size="xs" color="dimmed">Reason</Text>
                  <Text size="sm">{request.reason}</Text>
                </div>

                <Group spacing="sm">
                  <Button
                    size="sm"
                    color="green"
                    leftIcon={<IconCheck size={14} />}
                    onClick={() => {
                      setApproveModal({
                        open: true,
                        request: request,
                      });
                      setApproveForm({
                        approved_duration: request.requested_duration,
                        duration_modified_reason: '',
                      });
                    }}
                  >
                    Approve
                  </Button>
                  <Button
                    size="sm"
                    color="red"
                    leftIcon={<IconX size={14} />}
                    onClick={() => {
                      setRejectModal({ open: true, request: request });
                      setRejectForm({ rejection_reason: '' });
                    }}
                  >
                    Reject
                  </Button>
                  <Button
                    size="sm"
                    color="blue"
                    variant="light"
                    leftIcon={<IconEye size={14} />}
                    onClick={() => setDetailModal({ open: true, request: request })}
                  >
                    Details
                  </Button>
                </Group>
              </Stack>
            </Card>
          ))}
        </Stack>
      )}
    </Stack>
  );

  // All Requests Panel
  const AllRequestsPanel = () => (
    <Stack spacing="md">
      <Group position="apart">
        <Text size="lg" weight={500}>All Requests History</Text>
        <ActionIcon
          color="blue"
          onClick={handleRefresh}
          loading={refreshing}
        >
          <IconRefresh size={16} />
        </ActionIcon>
      </Group>

      {loading ? (
        <Loader />
      ) : (
        <Table striped highlightOnHover>
          <thead>
            <tr>
              <th>User</th>
              <th>Role</th>
              <th>Duration</th>
              <th>Status</th>
              <th>Requested</th>
              <th>Reviewed By</th>
              <th>Expires</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {allRequests.map((request) => (
              <tr key={request.id}>
                <td>{request.user}</td>
                <td>{request.role}</td>
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
                <td>{request.reviewed_by || 'N/A'}</td>
                <td>
                  {request.expires_at ? (
                    <Text size="sm">{getTimeRemaining(request.expires_at)}</Text>
                  ) : (
                    'N/A'
                  )}
                </td>
                <td>
                  <Group spacing={4}>
                    {request.status === 'APPROVED' && (
                      <ActionIcon
                        color="orange"
                        size="sm"
                        onClick={() => {
                          setWithdrawModal({ open: true, request: request });
                          setWithdrawForm({ revocation_reason: '' });
                        }}
                        title="Withdraw"
                      >
                        <IconX size={14} />
                      </ActionIcon>
                    )}
                    <ActionIcon
                      color="blue"
                      size="sm"
                      onClick={() => setDetailModal({ open: true, request: request })}
                      title="Details"
                    >
                      <IconEye size={14} />
                    </ActionIcon>
                  </Group>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
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
                <Title order={3}>Emergency Access Admin</Title>
                <Text size="sm" color="dimmed">
                  Review and manage emergency access requests
                </Text>
              </div>
            </Group>
            <Badge size="lg" color="red">
              <IconKey size={14} style={{ marginRight: 4 }} />
              Admin Panel
            </Badge>
          </Group>
        </Paper>

        {/* Stats */}
        <StatsPanel />

        {/* Tabs */}
        <Tabs value={activeTab} onTabChange={setActiveTab}>
          <Tabs.List>
            <Tabs.Tab value="pending" icon={<IconClock size={16} />}>
              Pending ({stats.pending})
            </Tabs.Tab>
            <Tabs.Tab value="all" icon={<IconHistory size={16} />}>
              All Requests ({allRequests.length})
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="pending" pt="md">
            <Paper shadow="xs" p="md" withBorder>
              <PendingRequestsPanel />
            </Paper>
          </Tabs.Panel>

          <Tabs.Panel value="all" pt="md">
            <Paper shadow="xs" p="md" withBorder>
              <AllRequestsPanel />
            </Paper>
          </Tabs.Panel>
        </Tabs>
      </Stack>

      {/* Approve Modal */}
      <Modal
        opened={approveModal.open}
        onClose={() => setApproveModal({ open: false, request: null })}
        title="Approve Emergency Access Request"
        size="md"
      >
        <Stack spacing="md">
          {approveModal.request && (
            <>
              <Alert icon={<IconAlertCircle size={16} />} color="blue">
                <Text><strong>User:</strong> {approveModal.request.user}</Text>
                <Text><strong>Role:</strong> {approveModal.request.role}</Text>
                <Text><strong>Requested Duration:</strong> {formatDuration(approveModal.request.requested_duration)}</Text>
              </Alert>

              <Stack spacing="sm">
                <NumberInput
                  label="Approved Duration (minutes)"
                  description="Leave empty to use requested duration, or modify as needed (max 1440 minutes = 24 hours)"
                  min={1}
                  max={1440}
                  value={approveForm.approved_duration}
                  onChange={(value) => setApproveForm({ ...approveForm, approved_duration: value })}
                />

                <Textarea
                  label="Reason for Duration Modification (optional)"
                  placeholder="Explain why you're modifying the duration"
                  minRows={2}
                  value={approveForm.duration_modified_reason}
                  onChange={(e) => setApproveForm({ ...approveForm, duration_modified_reason: e.currentTarget.value })}
                />

                <Group position="apart">
                  <Button
                    variant="default"
                    onClick={() => setApproveModal({ open: false, request: null })}
                  >
                    Cancel
                  </Button>
                  <Button
                    color="green"
                    onClick={handleApprove}
                    loading={loading}
                  >
                    Approve
                  </Button>
                </Group>
              </Stack>
            </>
          )}
        </Stack>
      </Modal>

      {/* Reject Modal */}
      <Modal
        opened={rejectModal.open}
        onClose={() => setRejectModal({ open: false, request: null })}
        title="Reject Emergency Access Request"
        size="md"
      >
        <Stack spacing="md">
          {rejectModal.request && (
            <>
              <Alert icon={<IconAlertCircle size={16} />} color="red">
                <Text><strong>User:</strong> {rejectModal.request.user}</Text>
                <Text><strong>Role:</strong> {rejectModal.request.role}</Text>
                <Text><strong>Reason:</strong> {rejectModal.request.reason}</Text>
              </Alert>

              <Stack spacing="sm">
                <Textarea
                  label="Rejection Reason (optional)"
                  placeholder="Provide a reason for rejection"
                  minRows={3}
                  value={rejectForm.rejection_reason}
                  onChange={(e) => setRejectForm({ ...rejectForm, rejection_reason: e.currentTarget.value })}
                />

                <Group position="apart">
                  <Button
                    variant="default"
                    onClick={() => setRejectModal({ open: false, request: null })}
                  >
                    Cancel
                  </Button>
                  <Button
                    color="red"
                    onClick={handleReject}
                    loading={loading}
                  >
                    Reject
                  </Button>
                </Group>
              </Stack>
            </>
          )}
        </Stack>
      </Modal>

      {/* Withdraw Modal */}
      <Modal
        opened={withdrawModal.open}
        onClose={() => setWithdrawModal({ open: false, request: null })}
        title="Withdraw Emergency Access"
        size="md"
      >
        <Stack spacing="md">
          {withdrawModal.request && (
            <>
              <Alert icon={<IconAlertCircle size={16} />} color="orange">
                <Text><strong>User:</strong> {withdrawModal.request.user}</Text>
                <Text><strong>Role:</strong> {withdrawModal.request.role}</Text>
                <Text><strong>Expires:</strong> {withdrawModal.request.expires_at ? new Date(withdrawModal.request.expires_at).toLocaleString() : 'N/A'}</Text>
              </Alert>

              <Stack spacing="sm">
                <Textarea
                  label="Revocation Reason (optional)"
                  placeholder="Provide a reason for withdrawal"
                  minRows={3}
                  value={withdrawForm.revocation_reason}
                  onChange={(e) => setWithdrawForm({ ...withdrawForm, revocation_reason: e.currentTarget.value })}
                />

                <Group position="apart">
                  <Button
                    variant="default"
                    onClick={() => setWithdrawModal({ open: false, request: null })}
                  >
                    Cancel
                  </Button>
                  <Button
                    color="orange"
                    onClick={handleWithdraw}
                    loading={loading}
                  >
                    Withdraw
                  </Button>
                </Group>
              </Stack>
            </>
          )}
        </Stack>
      </Modal>

      {/* Detail Modal */}
      <Modal
        opened={detailModal.open}
        onClose={() => setDetailModal({ open: false, request: null })}
        title="Request Details"
        size="lg"
      >
        {detailModal.request && (
          <Stack spacing="md">
            <Group spacing="xl">
              <div>
                <Text size="xs" color="dimmed">User</Text>
                <Text weight={500}>{detailModal.request.user}</Text>
              </div>
              <div>
                <Text size="xs" color="dimmed">Role</Text>
                <Text weight={500}>{detailModal.request.role}</Text>
              </div>
              <div>
                <Text size="xs" color="dimmed">Status</Text>
                {getStatusBadge(detailModal.request.status)}
              </div>
            </Group>

            <Stack spacing="xs">
              <div>
                <Text size="xs" color="dimmed">Reason</Text>
                <Text>{detailModal.request.reason}</Text>
              </div>

              <Group spacing="xl">
                <div>
                  <Text size="xs" color="dimmed">Requested Duration</Text>
                  <Text>{formatDuration(detailModal.request.requested_duration)}</Text>
                </div>
                <div>
                  <Text size="xs" color="dimmed">Approved Duration</Text>
                  <Text>{detailModal.request.approved_duration ? formatDuration(detailModal.request.approved_duration) : 'N/A'}</Text>
                </div>
              </Group>

              <Group spacing="xl">
                <div>
                  <Text size="xs" color="dimmed">Requested At</Text>
                  <Text>{new Date(detailModal.request.requested_at).toLocaleString()}</Text>
                </div>
                <div>
                  <Text size="xs" color="dimmed">Reviewed At</Text>
                  <Text>{detailModal.request.reviewed_at ? new Date(detailModal.request.reviewed_at).toLocaleString() : 'N/A'}</Text>
                </div>
              </Group>

              <Group spacing="xl">
                <div>
                  <Text size="xs" color="dimmed">Reviewed By</Text>
                  <Text>{detailModal.request.reviewed_by || 'N/A'}</Text>
                </div>
                <div>
                  <Text size="xs" color="dimmed">Expires At</Text>
                  <Text>{detailModal.request.expires_at ? new Date(detailModal.request.expires_at).toLocaleString() : 'N/A'}</Text>
                </div>
              </Group>

              {detailModal.request.rejection_reason && (
                <div>
                  <Text size="xs" color="dimmed">Rejection Reason</Text>
                  <Text color="red">{detailModal.request.rejection_reason}</Text>
                </div>
              )}

              {detailModal.request.duration_modified_reason && (
                <div>
                  <Text size="xs" color="dimmed">Duration Modification Reason</Text>
                  <Text color="orange">{detailModal.request.duration_modified_reason}</Text>
                </div>
              )}
            </Stack>
          </Stack>
        )}
      </Modal>
    </Container>
  );
}

export default EmergencyAccessAdminPage;

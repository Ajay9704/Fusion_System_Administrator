import React, { useState, useEffect } from 'react';
import {
    Container, Title, Paper, Stack, Group, Button, Text, TextInput,
    Select, Modal, Badge, Alert, LoadingOverlay, Grid, Card, Timeline
} from '@mantine/core';
import { IconClock, IconShield, IconAlertTriangle, IconCheck, IconX } from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { showErrorNotification, showSuccessNotification } from '../../utils/errorHandler';

const EmergencyAccessPage = () => {
    const { user } = useAuth();
    const isAdmin = user?.is_staff || user?.is_superuser;

    const [loading, setLoading] = useState(false);
    const [requests, setRequests] = useState([]);
    const [allRequests, setAllRequests] = useState([]); // For admin view
    const [requestHistory, setRequestHistory] = useState([]); // For past requests
    const [modalOpen, setModalOpen] = useState(false);
    const [approvalModalOpen, setApprovalModalOpen] = useState(false);
    const [selectedRequest, setSelectedRequest] = useState(null);
    const [approvalAction, setApprovalAction] = useState('');
    const [approvalReason, setApprovalReason] = useState('');
    const [formData, setFormData] = useState({
        role_id: '',
        reason: '',
        duration_hours: '24'
    });
    const [allRoles, setAllRoles] = useState([]);
    const [activeTab, setActiveTab] = useState('my-requests'); // 'my-requests', 'pending', 'all-history'

    const fetchRequests = async () => {
        setLoading(true);
        try {
            // Fetch only current user's own requests
            const response = await api.get('/emergency-access/requests/', {
                params: { view: 'my-requests' }
            });
            setRequests(response.data.requests || []);
        } catch (error) {
            showErrorNotification(error, 'Fetch Error');
        } finally {
            setLoading(false);
        }
    };

    const fetchAllRequests = async () => {
        if (!isAdmin) return;
        setLoading(true);
        try {
            // Fetch ALL requests for admin approval dashboard
            const response = await api.get('/emergency-access/requests/', {
                params: {
                    view: 'all-requests',
                    status: 'PENDING'
                }
            });
            setAllRequests(response.data.requests || []);
        } catch (error) {
            showErrorNotification(error, 'Fetch Error');
        } finally {
            setLoading(false);
        }
    };

    const fetchRequestHistory = async () => {
        if (!isAdmin) return;
        setLoading(true);
        try {
            // Fetch ALL past requests regardless of status
            const response = await api.get('/emergency-access/requests/', {
                params: {
                    view: 'all-requests',
                    status: 'ALL' // Get all statuses
                }
            });
            setRequestHistory(response.data.requests || []);
        } catch (error) {
            showErrorNotification(error, 'Fetch Error');
        } finally {
            setLoading(false);
        }
    };

    const fetchAllRoles = async () => {
        try {
            const response = await api.get('/view-roles/');
            setAllRoles(response.data || []);
        } catch (error) {
            console.error('Failed to fetch roles:', error);
        }
    };

    useEffect(() => {
        fetchRequests();
        fetchAllRoles();
        if (isAdmin) {
            fetchAllRequests();
            fetchRequestHistory();
        }
    }, []);

    const handleSubmitRequest = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            await api.post('/emergency-access/request/', {
                role_id: parseInt(formData.role_id),
                reason: formData.reason,
                duration_hours: parseInt(formData.duration_hours)
            });

            showSuccessNotification('Emergency access request submitted successfully');

            setModalOpen(false);
            setFormData({ role_id: '', reason: '', duration_hours: '24' });
            fetchRequests();
        } catch (error) {
            showErrorNotification(error, 'Request Failed');
        } finally {
            setLoading(false);
        }
    };

    const handleAction = async (requestId, action, reason = '') => {
        setLoading(true);
        try {
            if (action === 'activate') {
                await api.post(`/emergency-access/${requestId}/activate/`);
                showSuccessNotification('Emergency access is now active');
            } else if (action === 'revoke') {
                await api.post(`/emergency-access/${requestId}/revoke/`, { reason });
                showSuccessNotification('Emergency access has been revoked');
            }

            fetchRequests();
            if (isAdmin) fetchAllRequests();
        } catch (error) {
            showErrorNotification(error, 'Action Failed');
        } finally {
            setLoading(false);
        }
    };

    const handleApproval = async () => {
        if (!selectedRequest || !approvalAction) return;
        
        setLoading(true);
        try {
            await api.post(`/emergency-access/${selectedRequest.id}/approve/`, {
                action: approvalAction,
                reason: approvalReason
            });

            showSuccessNotification(
                approvalAction === 'approve' 
                    ? 'Emergency access request approved' 
                    : 'Emergency access request denied'
            );

            setApprovalModalOpen(false);
            setSelectedRequest(null);
            setApprovalAction('');
            setApprovalReason('');
            fetchAllRequests();
        } catch (error) {
            showErrorNotification(error, 'Approval Failed');
        } finally {
            setLoading(false);
        }
    };

    const openApprovalModal = (request, action) => {
        setSelectedRequest(request);
        setApprovalAction(action);
        setApprovalReason('');
        setApprovalModalOpen(true);
    };

    const getStatusBadge = (status) => {
        const statusConfig = {
            'PENDING': { color: 'yellow', icon: <IconClock size={14} /> },
            'APPROVED': { color: 'blue', icon: <IconShield size={14} /> },
            'ACTIVE': { color: 'green', icon: <IconCheck size={14} /> },
            'EXPIRED': { color: 'gray', icon: <IconX size={14} /> },
            'REVOKED': { color: 'red', icon: <IconX size={14} /> },
            'DENIED': { color: 'red', icon: <IconX size={14} /> }
        };

        const config = statusConfig[status] || statusConfig['PENDING'];
        return (
            <Badge
                color={config.color}
                leftSection={config.icon}
                variant="light"
            >
                {status.replace('_', ' ')}
            </Badge>
        );
    };

    const roleOptions = allRoles
        .filter(role => role.name && role.name !== 'student')
        .map(role => ({
            value: String(role.id),
            label: role.full_name || role.name
        }));

    return (
        <Container size="lg" py="xl">
            <LoadingOverlay visible={loading} />

            <Stack>
                <Group position="apart" align="center">
                    <Title order={2}>Emergency Access System</Title>
                    <Button
                        leftSection={<IconShield size={16} />}
                        onClick={() => setModalOpen(true)}
                    >
                        Request Emergency Access
                    </Button>
                </Group>

                <Alert icon={<IconAlertTriangle size={20} />} color="blue" title="Temporary Role Escalation">
                    Request temporary elevated permissions for critical situations. All requests are logged and require approval.
                </Alert>

                {/* Admin Tab Navigation */}
                {isAdmin && (
                    <Group spacing="md">
                        <Button
                            variant={activeTab === 'my-requests' ? 'filled' : 'light'}
                            onClick={() => setActiveTab('my-requests')}
                        >
                            My Requests
                        </Button>
                        <Button
                            variant={activeTab === 'all-requests' ? 'filled' : 'light'}
                            onClick={() => {
                                setActiveTab('all-requests');
                                fetchAllRequests();
                            }}
                        >
                            Pending Approvals ({allRequests.length})
                        </Button>
                        <Button
                            variant={activeTab === 'all-history' ? 'filled' : 'light'}
                            onClick={() => {
                                setActiveTab('all-history');
                                fetchRequestHistory();
                            }}
                        >
                            Request History ({requestHistory.length})
                        </Button>
                    </Group>
                )}

                {/* Admin View: Pending Approvals */}
                {isAdmin && activeTab === 'all-requests' && (
                    <Paper shadow="sm" p="md" withBorder>
                        <Title order={4} mb="md">Pending Approval Requests</Title>

                        {allRequests.length === 0 ? (
                            <Text color="dimmed" align="center" py="xl">
                                No pending requests to review
                            </Text>
                        ) : (
                            <Stack>
                                {allRequests.map((request) => (
                                    <Card key={request.id} p="md" withBorder>
                                        <Grid>
                                            <Grid.Col span={8}>
                                                <Stack spacing="xs">
                                                    <Group position="apart">
                                                        <div>
                                                            <Text weight={500}>
                                                                {request.requested_role.full_name}
                                                            </Text>
                                                            <Text size="sm" color="dimmed">
                                                                Requested by: {request.requester.username} ({request.requester.email})
                                                            </Text>
                                                        </div>
                                                        {getStatusBadge(request.status)}
                                                    </Group>

                                                    <Text size="sm" color="dimmed">
                                                        <strong>Reason:</strong> {request.reason}
                                                    </Text>

                                                    <Group spacing="xl">
                                                        <Text size="xs">
                                                            <strong>Duration:</strong> {request.duration_hours} hours
                                                        </Text>
                                                        <Text size="xs">
                                                            <strong>Requested:</strong> {new Date(request.created_at).toLocaleString()}
                                                        </Text>
                                                    </Group>
                                                </Stack>
                                            </Grid.Col>

                                            <Grid.Col span={4}>
                                                <Stack spacing="xs" align="flex-end">
                                                    {/* Hide approve/deny buttons if this is your own request */}
                                                    {request.requester.username !== user?.username ? (
                                                        <>
                                                            <Button
                                                                size="xs"
                                                                color="green"
                                                                leftSection={<IconCheck size={14} />}
                                                                onClick={() => openApprovalModal(request, 'approve')}
                                                            >
                                                                Approve
                                                            </Button>
                                                            <Button
                                                                size="xs"
                                                                color="red"
                                                                variant="light"
                                                                leftSection={<IconX size={14} />}
                                                                onClick={() => openApprovalModal(request, 'deny')}
                                                            >
                                                                Deny
                                                            </Button>
                                                        </>
                                                    ) : (
                                                        <Text size="xs" color="dimmed" style={{ fontStyle: 'italic' }}>
                                                            Your own request - requires another admin's approval
                                                        </Text>
                                                    )}
                                                </Stack>
                                            </Grid.Col>
                                        </Grid>
                                    </Card>
                                ))}
                            </Stack>
                        )}
                    </Paper>
                )}

                {/* Admin View: All Request History */}
                {isAdmin && activeTab === 'all-history' && (
                    <Paper shadow="sm" p="md" withBorder>
                        <Title order={4} mb="md">Complete Request History ({requestHistory.length})</Title>

                        {requestHistory.length === 0 ? (
                            <Text color="dimmed" align="center" py="xl">
                                No emergency access requests found in history
                            </Text>
                        ) : (
                            <Stack>
                                {requestHistory.map((request) => (
                                    <Card key={request.id} p="md" withBorder>
                                        <Grid>
                                            <Grid.Col span={8}>
                                                <Stack spacing="xs">
                                                    <Group position="apart">
                                                        <div>
                                                            <Text weight={500}>
                                                                {request.requested_role.full_name}
                                                            </Text>
                                                            <Text size="sm" color="dimmed">
                                                                Requested by: <strong>{request.requester.username}</strong> ({request.requester.email})
                                                            </Text>
                                                        </div>
                                                        {getStatusBadge(request.status)}
                                                    </Group>

                                                    <Text size="sm" color="dimmed">
                                                        <strong>Reason:</strong> {request.reason}
                                                    </Text>

                                                    <Group spacing="xl">
                                                        <Text size="xs">
                                                            <strong>Duration:</strong> {request.duration_hours} hours
                                                        </Text>
                                                        <Text size="xs">
                                                            <strong>Requested:</strong> {new Date(request.created_at).toLocaleString()}
                                                        </Text>
                                                        {request.reviewed_at && (
                                                            <Text size="xs">
                                                                <strong>Reviewed:</strong> {new Date(request.reviewed_at).toLocaleString()}
                                                            </Text>
                                                        )}
                                                    </Group>

                                                    {/* Show reviewer information for processed requests */}
                                                    {(request.status === 'APPROVED' || request.status === 'DENIED') && (
                                                        <Text size="xs" color="dimmed" style={{ backgroundColor: '#f8f9fa', padding: '8px', borderRadius: '4px' }}>
                                                            <strong>Reviewer:</strong> {request.reviewer || request.approver || 'N/A'}
                                                            {request.approval_reason && (
                                                                <>
                                                                    <br />
                                                                    <strong>{request.status === 'APPROVED' ? 'Approval' : 'Denial'} Reason:</strong> {request.approval_reason}
                                                                </>
                                                            )}
                                                        </Text>
                                                    )}

                                                    {request.activated_at && (
                                                        <Text size="xs" color="dimmed">
                                                            <strong>Activated:</strong> {new Date(request.activated_at).toLocaleString()}
                                                        </Text>
                                                    )}

                                                    {request.expires_at && (
                                                        <Text size="xs" color="dimmed">
                                                            <strong>Expires:</strong> {new Date(request.expires_at).toLocaleString()}
                                                        </Text>
                                                    )}

                                                    {request.revoked_at && (
                                                        <Text size="xs" color="dimmed">
                                                            <strong>Revoked:</strong> {new Date(request.revoked_at).toLocaleString()}
                                                            {request.approval_reason && request.status === 'REVOKED' && ` - Reason: ${request.approval_reason}`}
                                                        </Text>
                                                    )}
                                                </Stack>
                                            </Grid.Col>

                                            <Grid.Col span={4}>
                                                <Stack spacing="xs" align="flex-end">
                                                    {request.status === 'PENDING' && request.requester.username !== user?.username ? (
                                                        <>
                                                            <Button
                                                                size="xs"
                                                                color="green"
                                                                leftSection={<IconCheck size={14} />}
                                                                onClick={() => openApprovalModal(request, 'approve')}
                                                            >
                                                                Approve
                                                            </Button>
                                                            <Button
                                                                size="xs"
                                                                color="red"
                                                                variant="light"
                                                                leftSection={<IconX size={14} />}
                                                                onClick={() => openApprovalModal(request, 'deny')}
                                                            >
                                                                Deny
                                                            </Button>
                                                        </>
                                                    ) : request.status === 'PENDING' && request.requester.username === user?.username ? (
                                                        <Text size="xs" color="dimmed" style={{ fontStyle: 'italic' }}>
                                                            Your own request - requires another admin's approval
                                                        </Text>
                                                    ) : (
                                                        <Badge
                                                            size="sm"
                                                            color={
                                                                request.status === 'APPROVED' ? 'green' :
                                                                request.status === 'DENIED' ? 'red' :
                                                                request.status === 'ACTIVE' ? 'blue' : 'gray'
                                                            }
                                                            variant="light"
                                                        >
                                                            {request.status}
                                                        </Badge>
                                                    )}
                                                </Stack>
                                            </Grid.Col>
                                        </Grid>
                                    </Card>
                                ))}
                            </Stack>
                        )}
                    </Paper>
                )}

                {/* User View: My Requests */}
                {(!isAdmin || activeTab === 'my-requests') && (
                    <Paper shadow="sm" p="md" withBorder>
                        <Title order={4} mb="md">My Requests</Title>

                    {requests.length === 0 ? (
                        <Text color="dimmed" align="center" py="xl">
                            No emergency access requests found
                        </Text>
                    ) : (
                        <Stack>
                            {requests.map((request) => (
                                <Card key={request.id} p="md" withBorder>
                                    <Grid>
                                        <Grid.Col span={8}>
                                            <Stack spacing="xs">
                                                <Group position="apart">
                                                    <Text weight={500}>
                                                        {request.requested_role.full_name}
                                                    </Text>
                                                    {getStatusBadge(request.status)}
                                                </Group>

                                                <Text size="sm" color="dimmed">
                                                    {request.reason}
                                                </Text>

                                                <Group spacing="xl">
                                                    <Text size="xs">
                                                        <strong>Duration:</strong> {request.duration_hours} hours
                                                    </Text>
                                                    <Text size="xs">
                                                        <strong>Created:</strong> {new Date(request.created_at).toLocaleString()}
                                                    </Text>
                                                    {request.expires_at && (
                                                        <Text size="xs">
                                                            <strong>Expires:</strong> {new Date(request.expires_at).toLocaleString()}
                                                        </Text>
                                                    )}
                                                </Group>

                                                {request.approval_reason && (
                                                    <Text size="sm" c="dimmed">
                                                        <strong>Note:</strong> {request.approval_reason}
                                                    </Text>
                                                )}
                                            </Stack>
                                        </Grid.Col>

                                        <Grid.Col span={4}>
                                            <Group position="right" align="flex-start">
                                                {request.status === 'APPROVED' && (
                                                    <Button
                                                        size="xs"
                                                        color="green"
                                                        onClick={() => handleAction(request.id, 'activate')}
                                                    >
                                                        Activate
                                                    </Button>
                                                )}

                                                {request.status === 'ACTIVE' && (
                                                    <Button
                                                        size="xs"
                                                        color="red"
                                                        variant="light"
                                                        onClick={() => handleAction(request.id, 'revoke')}
                                                    >
                                                        Revoke
                                                    </Button>
                                                )}
                                            </Group>
                                        </Grid.Col>
                                    </Grid>
                                </Card>
                            ))}
                        </Stack>
                    )}
                </Paper>
                )}
            </Stack>

            <Modal
                opened={modalOpen}
                onClose={() => setModalOpen(false)}
                title="Request Emergency Access"
                centered
            >
                <form onSubmit={handleSubmitRequest}>
                    <Stack>
                        <Select
                            label="Role"
                            placeholder="Select role you need temporary access to"
                            required
                            searchable
                            data={roleOptions}
                            value={formData.role_id}
                            onChange={(value) => setFormData({ ...formData, role_id: value })}
                        />

                        <TextInput
                            label="Duration (hours)"
                            type="number"
                            required
                            value={formData.duration_hours}
                            onChange={(e) => setFormData({ ...formData, duration_hours: e.target.value })}
                            min="1"
                            max="168"
                            description="Maximum 168 hours (7 days)"
                        />

                        <TextInput
                            label="Reason"
                            placeholder="Explain why you need emergency access"
                            required
                            multiline
                            rows={3}
                            value={formData.reason}
                            onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                            description="This will be reviewed by administrators"
                        />

                        <Group position="right" mt="md">
                            <Button
                                variant="default"
                                onClick={() => setModalOpen(false)}
                                disabled={loading}
                            >
                                Cancel
                            </Button>
                            <Button
                                type="submit"
                                loading={loading}
                            >
                                Submit Request
                            </Button>
                        </Group>
                    </Stack>
                </form>
            </Modal>

            {/* Approval Modal for Admins */}
            <Modal
                opened={approvalModalOpen}
                onClose={() => setApprovalModalOpen(false)}
                title={approvalAction === 'approve' ? 'Approve Emergency Access' : 'Deny Emergency Access'}
                centered
            >
                {selectedRequest && (
                    <Stack>
                        <Paper p="md" withBorder>
                            <Stack spacing="xs">
                                <Text size="sm">
                                    <strong>Requester:</strong> {selectedRequest.requester.username}
                                </Text>
                                <Text size="sm">
                                    <strong>Role:</strong> {selectedRequest.requested_role.full_name}
                                </Text>
                                <Text size="sm">
                                    <strong>Reason:</strong> {selectedRequest.reason}
                                </Text>
                                <Text size="sm">
                                    <strong>Duration:</strong> {selectedRequest.duration_hours} hours
                                </Text>
                            </Stack>
                        </Paper>

                        <TextInput
                            label={approvalAction === 'approve' ? 'Approval Reason (optional)' : 'Denial Reason (required)'}
                            placeholder={approvalAction === 'approve' ? 'Add a note (optional)' : 'Explain why this request is denied'}
                            required={approvalAction === 'deny'}
                            multiline
                            rows={3}
                            value={approvalReason}
                            onChange={(e) => setApprovalReason(e.target.value)}
                        />

                        <Group position="right" mt="md">
                            <Button
                                variant="default"
                                onClick={() => setApprovalModalOpen(false)}
                                disabled={loading}
                            >
                                Cancel
                            </Button>
                            <Button
                                color={approvalAction === 'approve' ? 'green' : 'red'}
                                loading={loading}
                                onClick={handleApproval}
                            >
                                {approvalAction === 'approve' ? 'Approve' : 'Deny'} Request
                            </Button>
                        </Group>
                    </Stack>
                )}
            </Modal>
        </Container>
    );
};

export default EmergencyAccessPage;

import React, { useState, useMemo, useEffect } from "react";
import {
    Tabs, Card, Text, ScrollArea, Container, Title,
    Flex, Button, TextInput, MultiSelect, Grid, Paper,
    Center, Divider, Checkbox, Group, Modal, Loader, Stack,
    rem
} from "@mantine/core";
import { debounce } from "lodash";
import { FaCheck } from "react-icons/fa";
import { showNotification } from "@mantine/notifications";
import { fetchUsersByType, archiveUser } from "../../services/userService";
import { showErrorNotification, showSuccessNotification } from "../../utils/errorHandler";

const InfoCard = ({ person, selectable, selected, onSelectChange }) => (
    <Card shadow="sm" radius="xl" withBorder p="lg" style={{ backgroundColor: "#fdfdfd" }}>
        <Group position="apart" align="flex-start">
            <div style={{ flex: 1 }}>
                <Text fw={600} size="lg" mb="xs">{person.full_name}</Text>
                <Text size="sm" c="dimmed"><strong>Username:</strong> {person.username}</Text>
                <Divider my="sm" />
                <Text size="sm"><strong>Department:</strong> {person.department}</Text>
                <Text size="sm"><strong>Designation:</strong> {person.designations ? person.designations.join(', ') : 'N/A'}</Text>
                <Text size="sm"><strong>Gender:</strong> {person.gender}</Text>
            </div>
            {selectable && (
                <Checkbox
                    checked={selected}
                    onChange={() => onSelectChange(person.username)}
                    mt="sm"
                />
            )}
        </Group>
    </Card>
);

const extractUnique = (arr, key) => [...new Set(arr.map(item => String(item[key] || '')))];

const filterAndSearch = (data, filters, searchQuery) =>
    data.filter((person) => {
        const matchSearch = person.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            person.username.toLowerCase().includes(searchQuery.toLowerCase());

        const matchFilters = Object.entries(filters).every(([key, values]) => {
            if (values.length === 0) return true;
            return values.includes(String(person[key] || ''));
        });

        return matchSearch && matchFilters;
    });

const ArchiveFacultyPage = () => {
    const checkIcon = <FaCheck style={{ width: rem(20), height: rem(20) }} />;

    const [faculty, setFaculty] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState("archive");
    const [searchQuery, setSearchQuery] = useState("");
    const [filters, setFilters] = useState({
        department: [], designation: [], category: [], gender: []
    });
    const [selectedUsernames, setSelectedUsernames] = useState([]);
    const [modalOpened, setModalOpened] = useState(false);
    const [processingAction, setProcessingAction] = useState(false);

    const fetchFaculty = async () => {
        setLoading(true);
        try {
            const data = await fetchUsersByType('faculty');
            setFaculty(data || []);
        } catch (error) {
            showErrorNotification(error, 'Fetch Error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchFaculty();
    }, []);

    const handleSearchChange = useMemo(() =>
        debounce((value) => setSearchQuery(value), 200), []);

    const filteredData = useMemo(() =>
        filterAndSearch(faculty, filters, searchQuery),
        [faculty, filters, searchQuery]);

    const isSelected = (username) => selectedUsernames.includes(username);
    const toggleSelect = (username) => {
        setSelectedUsernames((prev) =>
            prev.includes(username) ? prev.filter(u => u !== username) : [...prev, username]
        );
    };

    const selectAll = () => {
        setSelectedUsernames(filteredData.map(u => u.username));
    };

    const clearSelection = () => setSelectedUsernames([]);

    const handleArchive = async () => {
        setProcessingAction(true);
        try {
            for (const username of selectedUsernames) {
                await archiveUser(username);
            }

            showSuccessNotification(`${selectedUsernames.length} faculty member(s) archived successfully`);

            await fetchFaculty();
            clearSelection();
            setModalOpened(false);
        } catch (error) {
            showErrorNotification(error, 'Archive Failed');
        } finally {
            setProcessingAction(false);
        }
    };

    return (
        <Container size="lg" py="xl">
            <Flex
                direction={{ base: 'column', sm: 'row' }}
                gap={{ base: 'sm', sm: 'lg' }}
                justify={{ sm: 'center' }}
                mb="xl"
            >
                <Button
                    variant="gradient"
                    size="xl"
                    radius="xs"
                    gradient={{ from: 'blue', to: 'cyan', deg: 90 }}
                    sx={{ display: 'block', width: { base: '100%', sm: 'auto' }, whiteSpace: 'normal', padding: '1rem', textAlign: 'center' }}
                >
                    <Title order={1} sx={{ fontSize: { base: 'lg', sm: 'xl' }, lineHeight: 1.2, wordBreak: 'break-word' }}>
                        Archive Faculty
                    </Title>
                </Button>
            </Flex>

            <Paper shadow="lg" p="xl" radius="xl" withBorder>
                {loading ? (
                    <Center style={{ minHeight: 400 }}>
                        <Stack align="center">
                            <Loader size="xl" color="blue" />
                            <Text color="dimmed">Loading faculty...</Text>
                        </Stack>
                    </Center>
                ) : (
                    <Tabs value={activeTab} onChange={setActiveTab} variant="pills" color="blue" radius="lg" keepMounted={false}>
                        <Tabs.List grow mb="lg">
                            <Tabs.Tab value="archive">ARCHIVE</Tabs.Tab>
                            <Tabs.Tab value="archived">ARCHIVED</Tabs.Tab>
                        </Tabs.List>

                        <Tabs.Panel value="archive">
                            <Grid mb="lg">
                                <Grid.Col span={12}>
                                    <TextInput
                                        placeholder="🔍 Search faculty"
                                        radius="md"
                                        onChange={(e) => handleSearchChange(e.currentTarget.value)}
                                    />
                                </Grid.Col>
                                {["department", "designation", "category", "gender"].map((key) => (
                                    <Grid.Col span={6} key={key}>
                                        <MultiSelect
                                            label={key[0].toUpperCase() + key.slice(1)}
                                            placeholder={`Filter by ${key}`}
                                            value={filters[key]}
                                            onChange={(value) => setFilters((prev) => ({ ...prev, [key]: value }))}
                                            data={extractUnique(faculty, key)}
                                            radius="md"
                                            searchable
                                            clearable
                                        />
                                    </Grid.Col>
                                ))}
                            </Grid>

                            <Group mb="md">
                                <Button onClick={selectAll} variant="light">Select All</Button>
                                <Button onClick={clearSelection} variant="default">Clear Selection</Button>
                            </Group>

                            <ScrollArea h={400}>
                                <Grid>
                                    {filteredData.map((faculty) => (
                                        <Grid.Col span={12} key={faculty.username}>
                                            <InfoCard
                                                person={faculty}
                                                selectable
                                                selected={isSelected(faculty.username)}
                                                onSelectChange={toggleSelect}
                                            />
                                        </Grid.Col>
                                    ))}
                                </Grid>
                            </ScrollArea>

                            {selectedUsernames.length > 0 && (
                                <Group mt="lg" position="right">
                                    <Button color="blue" onClick={() => setModalOpened(true)}>Archive</Button>
                                </Group>
                            )}
                        </Tabs.Panel>

                        <Tabs.Panel value="archived">
                            <Title order={3} mb="md">Recently Archived</Title>
                            <Grid>
                                {faculty.filter(f => !f.is_active).slice(0, 10).map((s) => (
                                    <Grid.Col span={12} key={s.username}>
                                        <InfoCard person={s} />
                                    </Grid.Col>
                                ))}
                                {faculty.filter(f => !f.is_active).length === 0 && (
                                    <Grid.Col span={12}>
                                        <Text color="dimmed">No archived faculty found</Text>
                                    </Grid.Col>
                                )}
                            </Grid>
                        </Tabs.Panel>
                    </Tabs>
                )}
            </Paper>

            <Modal
                opened={modalOpened}
                onClose={() => !processingAction && setModalOpened(false)}
                title="Confirm Archive"
                closeOnClickOutside={!processingAction}
            >
                <Text size="sm">Are you sure you want to archive {selectedUsernames.length} selected faculty member(s)?</Text>
                <Group position="right" mt="md">
                    <Button variant="outline" onClick={() => setModalOpened(false)} disabled={processingAction}>Cancel</Button>
                    <Button color="blue" onClick={handleArchive} loading={processingAction}>
                        {processingAction ? 'Archiving...' : 'Confirm'}
                    </Button>
                </Group>
            </Modal>
        </Container>
    );
};

export default ArchiveFacultyPage;

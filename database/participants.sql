SELECT users.name
FROM registrations
JOIN users ON registrations.user_id = users.id
WHERE registrations.event_id = :event_id
ORDER BY users.name;
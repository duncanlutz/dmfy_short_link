get_link_by_short_slug = '''SELECT old_long_slug AS url,
id AS link_id
FROM shortened_link
WHERE short_slug = %s;
'''

add_short_link_visit = '''INSERT INTO shortened_link_visit(
    {}
)
VALUES(
    {}
);
'''

get_affiliate_link_by_id = '''

'''
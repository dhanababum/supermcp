#!/bin/sh
set -e


echo "Configuring frontend with API_BASE_URL: $API_BASE_URL"

# # Create runtime config file
# apply env variables to the template without using envsubst
cp /usr/share/caddy/env-config.js.template /usr/share/caddy/env-config.js
# not working fix it
sed -i "s|\${API_BASE_URL}|${API_BASE_URL}|g" /usr/share/caddy/env-config.js
cat /usr/share/caddy/env-config.js
echo "Frontend configuration complete!"

# Execute the CMD (caddy run)
exec "$@"
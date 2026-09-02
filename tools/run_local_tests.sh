#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
lock_dir="/tmp/avaj-ros-test-domains"
mkdir -p "${lock_dir}"

domain_id=""
domain_count=53
domain_offset=$((BASHPID % domain_count))
for step in $(seq 0 $((domain_count - 1))); do
  candidate=$((180 + (domain_offset + step) % domain_count))
  exec 9>"${lock_dir}/domain-${candidate}.lock"
  if flock -n 9; then
    domain_id="${candidate}"
    break
  fi
  exec 9>&-
done

if [[ -z "${domain_id}" ]]; then
  echo "No free valid ROS_DOMAIN_ID in 180..232" >&2
  exit 2
fi

cleanup() {
  exec 9>&-
}
trap cleanup EXIT INT TERM

echo "AP-T01 isolated ROS_DOMAIN_ID=${domain_id}"

docker compose -f "${repo_dir}/compose.yaml" run --rm --no-deps \
  -e "ROS_DOMAIN_ID=${domain_id}" \
  -e "ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST" \
  jazzy bash -lc '
    set -eo pipefail
    cd /workspace
    source /opt/ros/jazzy/setup.bash
    colcon build --symlink-install --packages-select \
      rc_car_interfaces rc_car_usb_bridge avaj_sensor_processing \
      avaj_car_control
    source install/setup.bash
    set -u
    timeout --signal=INT --kill-after=10s 180s \
      colcon test --executor sequential --packages-select \
        rc_car_usb_bridge avaj_sensor_processing avaj_car_control \
        --event-handlers console_direct+
    colcon test-result --test-result-base build/rc_car_usb_bridge --verbose
    colcon test-result --test-result-base build/avaj_sensor_processing --verbose
    colcon test-result --test-result-base build/avaj_car_control --verbose
  '

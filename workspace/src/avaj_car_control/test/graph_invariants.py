#!/usr/bin/env python3
"""Observe the local ROS graph and enforce project publisher invariants."""

import argparse
import json
import time
from dataclasses import dataclass

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy

from tf2_msgs.msg import TFMessage


@dataclass(frozen=True)
class InvariantReport:
    """Serializable result from one bounded graph observation."""

    drive_publishers: tuple
    ackermann_publishers: tuple
    map_odom_publisher_count: int
    violations: tuple

    @property
    def ok(self):
        """Return whether all configured invariants passed."""
        return not self.violations

    def as_dict(self):
        """Convert the report to stable JSON-compatible values."""
        return {
            'ok': self.ok,
            'drive_publishers': list(self.drive_publishers),
            'ackermann_publishers': list(self.ackermann_publishers),
            'map_odom_publisher_count': self.map_odom_publisher_count,
            'violations': list(self.violations),
        }


class GraphInvariantMonitor(Node):
    """Collect endpoint identities and map-to-odom transform authorities."""

    def __init__(self, context=None, global_tf_nodes=None):
        """Create a simulation-time-aware, hardware-independent monitor."""
        super().__init__(
            'graph_invariant_monitor',
            context=context,
            parameter_overrides=[
                rclpy.parameter.Parameter(
                    'use_sim_time',
                    rclpy.Parameter.Type.BOOL,
                    True,
                ),
            ],
        )
        self._map_odom_observed = False
        self._global_tf_nodes = frozenset(
            global_tf_nodes or ('/slam_toolbox', '/amcl')
        )
        volatile_qos = QoSProfile(depth=100)
        volatile_qos.reliability = ReliabilityPolicy.BEST_EFFORT
        static_qos = QoSProfile(depth=100)
        static_qos.reliability = ReliabilityPolicy.RELIABLE
        static_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self.create_subscription(
            TFMessage, '/tf', self._on_tf, volatile_qos
        )
        self.create_subscription(
            TFMessage, '/tf_static', self._on_tf, static_qos
        )

    def _on_tf(self, message):
        for transform in message.transforms:
            parent = transform.header.frame_id.lstrip('/')
            child = transform.child_frame_id.lstrip('/')
            if parent == 'map' and child == 'odom':
                self._map_odom_observed = True

    @staticmethod
    def _endpoint_names(endpoints):
        return tuple(sorted({
            f'{info.node_namespace.rstrip("/")}/{info.node_name}'
            if info.node_namespace != '/'
            else f'/{info.node_name}'
            for info in endpoints
        }))

    def report(
        self,
        require_drive_commander=True,
        require_ackermann_controller=False,
    ):
        """Evaluate all three global publisher invariants."""
        drive = self._endpoint_names(
            self.get_publishers_info_by_topic('/drive_commands')
        )
        ackermann = self._endpoint_names(
            self.get_publishers_info_by_topic(
                '/control/autonomous_ackermann_cmd'
            )
        )
        tf_publishers = set(self._endpoint_names(
            self.get_publishers_info_by_topic('/tf')
        ))
        tf_publishers.update(self._endpoint_names(
            self.get_publishers_info_by_topic('/tf_static')
        ))
        map_odom_publishers = tuple(sorted(
            tf_publishers.intersection(self._global_tf_nodes)
        ))
        violations = []
        if require_drive_commander and drive != ('/drive_commander',):
            violations.append(
                '/drive_commands must have exactly /drive_commander as '
                f'publisher; observed {drive}'
            )
        elif not require_drive_commander and len(drive) > 1:
            violations.append(
                '/drive_commands has more than one publisher: '
                f'{drive}'
            )
        if len(ackermann) > 1:
            violations.append(
                '/control/autonomous_ackermann_cmd has more than one '
                f'publisher: {ackermann}'
            )
        if require_ackermann_controller and len(ackermann) != 1:
            violations.append(
                '/control/autonomous_ackermann_cmd must have exactly one '
                f'publisher; observed {ackermann}'
            )
        if len(map_odom_publishers) > 1:
            violations.append(
                'map -> odom was observed from more than one publisher: '
                f'{map_odom_publishers}'
            )
        if self._map_odom_observed and not map_odom_publishers:
            violations.append(
                'map -> odom was observed, but its publisher is not in the '
                'configured global TF node set'
            )
        return InvariantReport(
            drive,
            ackermann,
            len(map_odom_publishers),
            tuple(violations),
        )


def parse_args(args=None):
    """Parse the bounded standalone monitor options."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--observe-seconds', type=float, default=2.0)
    parser.add_argument(
        '--allow-no-drive-commander',
        action='store_true',
        help='permit zero /drive_commands publishers, but never two',
    )
    parser.add_argument(
        '--global-tf-node',
        action='append',
        dest='global_tf_nodes',
        help=(
            'fully qualified node allowed to own map -> odom; repeat for '
            'each configured mapping/localization provider'
        ),
    )
    parser.add_argument(
        '--require-autonomous-controller',
        action='store_true',
        help='require exactly one autonomous Ackermann publisher',
    )
    return parser.parse_args(args)


def main(args=None):
    """Run a bounded observation and return nonzero for any violation."""
    options = parse_args(args)
    if options.observe_seconds <= 0.0:
        raise SystemExit('--observe-seconds must be positive')
    context = rclpy.context.Context()
    rclpy.init(context=context)
    monitor = GraphInvariantMonitor(
        context=context,
        global_tf_nodes=options.global_tf_nodes,
    )
    executor = SingleThreadedExecutor(context=context)
    executor.add_node(monitor)
    try:
        deadline = time.monotonic() + options.observe_seconds
        while time.monotonic() < deadline:
            executor.spin_once(timeout_sec=0.05)
        report = monitor.report(
            require_drive_commander=not options.allow_no_drive_commander,
            require_ackermann_controller=(
                options.require_autonomous_controller
            ),
        )
        print(json.dumps(report.as_dict(), sort_keys=True))
        return 0 if report.ok else 1
    except KeyboardInterrupt:
        print(json.dumps({'ok': False, 'interrupted': True}))
        return 130
    finally:
        executor.remove_node(monitor)
        monitor.destroy_node()
        executor.shutdown()
        rclpy.shutdown(context=context)


if __name__ == '__main__':
    raise SystemExit(main())

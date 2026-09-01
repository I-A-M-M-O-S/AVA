#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to avaj_car_control__msg__DriveCommand
/// Normalized driver input. Every value is limited to the inclusive range 0..100.
/// steering:    0 = fully left, 50 = straight, 100 = fully right
/// acceleration: 0 = full reverse, 50 = neutral, 100 = full forward

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DriveCommand {

    // This member is not documented.
    #[allow(missing_docs)]
    pub steering: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub acceleration: u8,

}



impl Default for DriveCommand {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::DriveCommand::default())
  }
}

impl rosidl_runtime_rs::Message for DriveCommand {
  type RmwMsg = super::msg::rmw::DriveCommand;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        steering: msg.steering,
        acceleration: msg.acceleration,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      steering: msg.steering,
      acceleration: msg.acceleration,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      steering: msg.steering,
      acceleration: msg.acceleration,
    }
  }
}



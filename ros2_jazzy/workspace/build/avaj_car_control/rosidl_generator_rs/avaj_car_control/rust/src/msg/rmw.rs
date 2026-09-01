#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "avaj_car_control__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__avaj_car_control__msg__DriveCommand() -> *const std::ffi::c_void;
}

#[link(name = "avaj_car_control__rosidl_generator_c")]
extern "C" {
    fn avaj_car_control__msg__DriveCommand__init(msg: *mut DriveCommand) -> bool;
    fn avaj_car_control__msg__DriveCommand__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DriveCommand>, size: usize) -> bool;
    fn avaj_car_control__msg__DriveCommand__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DriveCommand>);
    fn avaj_car_control__msg__DriveCommand__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DriveCommand>, out_seq: *mut rosidl_runtime_rs::Sequence<DriveCommand>) -> bool;
}

// Corresponds to avaj_car_control__msg__DriveCommand
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// Normalized driver input. Every value is limited to the inclusive range 0..100.
/// steering:    0 = fully left, 50 = straight, 100 = fully right
/// acceleration: 0 = full reverse, 50 = neutral, 100 = full forward

#[repr(C)]
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
    unsafe {
      let mut msg = std::mem::zeroed();
      if !avaj_car_control__msg__DriveCommand__init(&mut msg as *mut _) {
        panic!("Call to avaj_car_control__msg__DriveCommand__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DriveCommand {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { avaj_car_control__msg__DriveCommand__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { avaj_car_control__msg__DriveCommand__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { avaj_car_control__msg__DriveCommand__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DriveCommand {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DriveCommand where Self: Sized {
  const TYPE_NAME: &'static str = "avaj_car_control/msg/DriveCommand";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__avaj_car_control__msg__DriveCommand() }
  }
}



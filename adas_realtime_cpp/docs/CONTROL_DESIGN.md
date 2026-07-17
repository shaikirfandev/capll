# Control and Estimation Design

## Signals and conventions

SI units are mandatory. Positive longitudinal acceleration propels the ego vehicle; negative acceleration requests braking. `LeadObject::relative_speed_mps` is lead speed minus ego speed, so a closing target has a negative value. Positive lane offset and heading error mean the ego vehicle is right of lane centre/direction. All external adapters must explicitly convert their signal convention to these definitions.

## Range state estimator

The filter state is $x = [r, \dot r]^T$, with the constant-velocity prediction model:

$$x_{k+1} = \begin{bmatrix}1 & \Delta t\\0 & 1\end{bmatrix}x_k + w_k$$

Radar/camera tracking provides range and range-rate measurements. The implementation uses scalar sequential updates to avoid an external matrix library. Production fusion must add association, outlier gating (for example normalized innovation squared), sensor-specific covariance, track lifecycle management, and time alignment. Never use an unvalidated object track to trigger braking.

## ACC policy

The desired gap is:

$$d_\mathrm{desired}=d_0 + T v_\mathrm{ego}$$

where $d_0=5$ m and $T=1.8$ s in the reference calibration. The controller limits the set speed by a gap-closing term and regulates the result with an anti-windup PID. Calibration must account for drivetrain delay, grade, brake blending, comfort limits, jerk limits, and legal requirements.

## AEB envelope

Closing speed is $v_c = \max(-\dot r, 0)$. The reference uses TTC $=r/v_c$ and an idealized braking-distance screen $d_b=v_c^2/(2|a_\min|)$. It commands a strong braking request below threshold. A production AEB stack needs a collision model, object classification, latency compensation, driver-brake blending, false-positive analysis, alert stage, arbitration, and a separate independent monitor.

## Lane centring and MPC

Preview error combines lateral and heading error:

$$e = y + L(v)\psi$$

The PID lane controller commands steering angle, then a rate limiter bounds steering increments. It is retained as a deterministic fallback by setting `use_mpc_lateral` to `false`.

The default controller is a fixed-horizon finite-control-set MPC. At each cycle it evaluates five steering-rate-limited candidate inputs through a kinematic bicycle prediction for 12 steps and selects the smallest weighted lateral-error, heading-error, steering-effort, and steering-change cost. Thus, its upper execution bound is $5 \times 12$ state updates with no heap allocation or iterative solver.

This compact MPC is an integration baseline, not a replacement for a vehicle-specific constrained MPC design. A series-production controller must use a verified vehicle/tyre model, road curvature preview, actuator delay model, friction constraints, driver-torque overlay, formal feasibility behavior, and target WCET evidence.

## Limits and calibration ownership

`Limits` is a safety-relevant parameter set. It must be configuration-controlled, versioned, range-checked at startup, and traceable to vehicle-level requirements. Parameter changes require regression, HIL, and safety review.

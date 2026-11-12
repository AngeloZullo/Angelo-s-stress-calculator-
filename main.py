from dataclasses import dataclass
from bakery import assert_equal
from drafter import (
    route,
    start_server,
    Page,
    Header,
    Text,
    Button,
    TextBox,
    SelectBox,
    CheckBox,
    LineBreak,
    set_website_title,
    set_site_information,
    hide_debug_information,
    set_website_framed,
)

# Site Configuration for GitHub Pages Deployment
set_website_title("MechE Stress & Safety Calculator")
set_site_information(
    author="Angelo Zullo",
    description=(
        "A mechanical engineering stress and factor of safety calculator "
        "built to help students verify structural designs."
    ),
    sources="Drafter documentation and CISC 106 course notes.",
    planning=["week10_brainstorming.docx"],
    links=["https://github.com/your-username/your-repository"],
)
hide_debug_information()
set_website_framed(False)


@dataclass
class Material:
    """Represents an engineering material and its yield strength in MPa."""

    name: str
    yield_strength: float


@dataclass
class State:
    """Stores the application state across routes."""

    materials: list[Material]
    history: list[str]
    last_result: str
    required_fos: float


DEFAULT_MATERIALS: list[Material] = [
    Material("Structural Steel (A36)", 250.0),
    Material("Aluminum 6061-T6", 276.0),
    Material("Titanium (Ti-6Al-4V)", 880.0),
    Material("Cast Iron (Gray)", 130.0),
]


def get_material_names(materials: list[Material]) -> list[str]:
    """Return a list of material names for the SelectBox dropdown."""
    names: list[str] = []
    for mat in materials:
        names.append(mat.name)
    return names


def find_yield_strength(materials: list[Material], target_name: str) -> float:
    """Find and return the yield strength (MPa) of a material by name."""
    for mat in materials:
        if mat.name == target_name:
            return mat.yield_strength
    return 0.0


def compute_stress_mpa(
    force_n: float, area_val: float, use_square_meters: bool
) -> float:
    """Calculate normal stress in MPa from force (N) and cross-sectional area."""
    if use_square_meters:
        # 1 Pa = 1 N/m^2, and 1 MPa = 1,000,000 Pa
        stress_pa: float = force_n / area_val
        return round(stress_pa / 1_000_000.0, 2)
    # 1 N/mm^2 is equal to 1 MPa
    return round(force_n / area_val, 2)


@route
def index(state: State) -> Page:
    """Display the main stress and factor of safety calculator page."""
    material_names: list[str] = get_material_names(state.materials)
    return Page(
        state,
        [
            Header("Mechanical Engineering Stress Calculator"),
            Text(
                "Enter an applied force, cross-sectional area, and material "
                "to check if your design is safe."
            ),
            LineBreak(),
            Text("Select Material:"),
            SelectBox("material_name", material_names, material_names[0]),
            LineBreak(),
            Text("Applied Force (in Newtons, N):"),
            TextBox("force_str", "5000"),
            LineBreak(),
            Text("Cross-Sectional Area (default is mm^2):"),
            TextBox("area_str", "50"),
            LineBreak(),
            CheckBox("use_meters", False),
            Text("Check if your area above is in m^2 instead of mm^2"),
            LineBreak(),
            Text("Target Minimum Factor of Safety (e.g., 1.5 or 2.0):"),
            TextBox("target_fos_str", str(state.required_fos)),
            LineBreak(),
            Button("Calculate Stress & Safety", calculate_stress),
            LineBreak(),
            Header("Navigation", 3),
            Button("View Calculation History", view_history),
            Button("Material Properties Table", view_materials),
            Button("Add Custom Material", add_material_page),
            Button("Formulas & How It Works", about_formulas),
        ],
    )


@route
def calculate_stress(
    state: State,
    material_name: str,
    force_str: str,
    area_str: str,
    use_meters: bool,
    target_fos_str: str,
) -> Page:
    """Validate inputs, calculate stress and factor of safety, and show result."""
    force_n: float = float(force_str)
    area_val: float = float(area_str)
    target_fos: float = float(target_fos_str)

    if force_n <= 0 or area_val <= 0 or target_fos <= 0:
        return Page(
            state,
            [
                Header("Invalid Input Error"),
                Text("Force, area, and target Factor of Safety must be > 0."),
                Button("Back to Calculator", index),
            ],
        )

    state.required_fos = target_fos
    stress_mpa: float = compute_stress_mpa(force_n, area_val, use_meters)
    strength_mpa: float = find_yield_strength(state.materials, material_name)

    if stress_mpa == 0.0:
        fos: float = 999.0
    else:
        fos = round(strength_mpa / stress_mpa, 2)

    if fos >= state.required_fos:
        status: str = "SAFE (Meets target Factor of Safety)"
    else:
        status = "UNSAFE (Below target Factor of Safety — risk of yielding!)"

    summary: str = (
        f"{material_name} | Force: {force_n} N | Stress: {stress_mpa} MPa | "
        f"FoS: {fos} -> {status}"
    )
    state.last_result = summary
    state.history.append(summary)

    return Page(
        state,
        [
            Header("Design Analysis Result"),
            Text(f"Selected Material: {material_name}"),
            Text(f"Material Yield Strength: {strength_mpa} MPa"),
            Text(f"Calculated Stress: {stress_mpa} MPa"),
            Text(f"Calculated Factor of Safety (FoS): {fos}"),
            Text(f"Target Minimum FoS: {state.required_fos}"),
            LineBreak(),
            Header(f"Verdict: {status}", 3),
            LineBreak(),
            Button("Run Another Calculation", index),
            Button("View All Past Calculations", view_history),
        ],
    )


@route
def view_history(state: State) -> Page:
    """Display all calculations performed during this session."""
    items: list = [Header("Calculation History")]
    if len(state.history) == 0:
        items.append(Text("No calculations recorded yet."))
    else:
        for entry in state.history:
            items.append(Text(f"- {entry}"))
    items.append(LineBreak())
    items.append(Button("Clear History", clear_history))
    items.append(Button("Back to Calculator", index))
    return Page(state, items)


@route
def clear_history(state: State) -> Page:
    """Clear the list of saved calculation history entries."""
    state.history = []
    state.last_result = "History cleared."
    return Page(
        state,
        [
            Header("History Cleared"),
            Text("All previous calculation logs have been removed."),
            Button("Back to Calculator", index),
        ],
    )


@route
def view_materials(state: State) -> Page:
    """Display all available engineering materials and their yield strengths."""
    items: list = [
        Header("Material Yield Strength Reference"),
        Text("Yield strength is the stress at which a material begins to deform."),
        LineBreak(),
    ]
    for mat in state.materials:
        items.append(Text(f"{mat.name}: {mat.yield_strength} MPa"))
    items.append(LineBreak())
    items.append(Button("Add a Custom Material", add_material_page))
    items.append(Button("Back to Calculator", index))
    return Page(state, items)


@route
def add_material_page(state: State) -> Page:
    """Display a form allowing the user to add a new material to the list."""
    return Page(
        state,
        [
            Header("Add Custom Engineering Material"),
            Text("Material Name (e.g., Copper C11000):"),
            TextBox("new_name", ""),
            LineBreak(),
            Text("Yield Strength (in MPa):"),
            TextBox("new_strength_str", "200"),
            LineBreak(),
            Button("Save Material", save_new_material),
            Button("Cancel", index),
        ],
    )


@route
def save_new_material(
    state: State, new_name: str, new_strength_str: str
) -> Page:
    """Validate and append a new Material instance to state.materials."""
    clean_name: str = new_name.strip()
    strength_val: float = float(new_strength_str)

    if clean_name == "" or strength_val <= 0:
        return Page(
            state,
            [
                Header("Invalid Material Entry"),
                Text("Please enter a valid name and a yield strength > 0 MPa."),
                Button("Try Again", add_material_page),
                Button("Back to Calculator", index),
            ],
        )

    state.materials.append(Material(clean_name, strength_val))
    return view_materials(state)


@route
def about_formulas(state: State) -> Page:
    """Explain the mechanics of materials formulas used in this app."""
    return Page(
        state,
        [
            Header("Mechanics of Materials: Formulas"),
            Text("1. Normal Stress (sigma) = Force (F) / Area (A)"),
            Text("   - 1 N / mm^2 equals 1 Megapascal (MPa)."),
            Text("   - 1 N / m^2 equals 1 Pascal (Pa) = 0.000001 MPa."),
            LineBreak(),
            Text("2. Factor of Safety (FoS) = Yield Strength / Calculated Stress"),
            Text("   - If FoS >= Target FoS, the part resists permanent bending."),
            Text("   - If FoS < Target FoS, the design is unsafe."),
            LineBreak(),
            Button("Back to Calculator", index),
        ],
    )


# --- Unit Tests ---
assert_equal(
    get_material_names(DEFAULT_MATERIALS),
    [
        "Structural Steel (A36)",
        "Aluminum 6061-T6",
        "Titanium (Ti-6Al-4V)",
        "Cast Iron (Gray)",
    ],
)
assert_equal(find_yield_strength(DEFAULT_MATERIALS, "Aluminum 6061-T6"), 276.0)
assert_equal(find_yield_strength(DEFAULT_MATERIALS, "Unknown"), 0.0)
assert_equal(compute_stress_mpa(5000.0, 50.0, False), 100.0)
assert_equal(compute_stress_mpa(5000000.0, 1.0, True), 5.0)

test_state = State(
    [Material("Structural Steel (A36)", 250.0)], [], "None", 1.5
)
assert_equal(isinstance(index(test_state), Page), True)
assert_equal(
    isinstance(
        calculate_stress(
            test_state, "Structural Steel (A36)", "5000", "50", False, "2.0"
        ),
        Page,
    ),
    True,
)
assert_equal(test_state.required_fos, 2.0)
assert_equal(len(test_state.history), 1)
assert_equal(isinstance(view_history(test_state), Page), True)
assert_equal(isinstance(clear_history(test_state), Page), True)
assert_equal(len(test_state.history), 0)
assert_equal(isinstance(view_materials(test_state), Page), True)
assert_equal(isinstance(add_material_page(test_state), Page), True)
assert_equal(
    isinstance(save_new_material(test_state, "Brass", "200"), Page), True
)
assert_equal(len(test_state.materials), 2)
assert_equal(isinstance(about_formulas(test_state), Page), True)


if __name__ == "__main__":
    start_server(State(list(DEFAULT_MATERIALS), [], "None", 1.5))

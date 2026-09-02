// Fail-closed W33 deployment-profile admission predicate.
// requested_carrier/host_carrier: 0 = circuit216/ST81, 1 = pair216/ST64.
// clifford_ns and weyl_ns are externally bound namespace identifiers; they
// must remain distinct because Sp(4,3) and PGSp(4,3) have equal order but are
// different execution/control domains.
module w33_profile_admission(
    input  wire        profile_valid,
    input  wire        requested_carrier,
    input  wire        host_carrier,
    input  wire [15:0] clifford_ns,
    input  wire [15:0] weyl_ns,
    output wire        admit
);
    wire carrier_match = (requested_carrier == host_carrier);
    wire namespace_separated = (clifford_ns != weyl_ns);

    assign admit = profile_valid && carrier_match && namespace_separated;

`ifdef FORMAL
    always @* begin
        assert(admit == (profile_valid && carrier_match && namespace_separated));
        if (admit) begin
            assert(profile_valid);
            assert(requested_carrier == host_carrier);
            assert(clifford_ns != weyl_ns);
        end
        if (!profile_valid)
            assert(!admit);
        if (requested_carrier != host_carrier)
            assert(!admit);
        if (clifford_ns == weyl_ns)
            assert(!admit);
    end
`endif
endmodule

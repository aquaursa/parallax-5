"""parallax5: The PARALLAX-5 reference CLI.

A single pip-installable command that wraps every operation a
protocol team, auditor, insurer, or AI-agent platform needs:

  parallax5 validate <cert>          Validate a certificate
  parallax5 init [--level P0..P5]    Wizard to author a new certificate
  parallax5 score <path>             Auto-issue cert from existing tool runs
  parallax5 quote --tvl ... --level  Premium estimate
  parallax5 doctor <path>            Diagnose what level a repo qualifies for
  parallax5 schema                   Print the JSON Schema
  parallax5 example                  Print the example certificate
  parallax5 catalog                  Browse the 53-incident catalog
"""

__version__ = "1.0.0"

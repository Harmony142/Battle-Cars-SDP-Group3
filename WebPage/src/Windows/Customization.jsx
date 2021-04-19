import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import InputLabel from '@material-ui/core/InputLabel';
import MenuItem from '@material-ui/core/MenuItem';
import FormControl from '@material-ui/core/FormControl';
import Select from '@material-ui/core/Select';

// UI components and example from https://material-ui.com/components/selects/#ControlledOpenSelect.js

const useStyles = makeStyles((theme) => ({
  button: {
    display: 'block',
    marginTop: theme.spacing(2),
  },
  formControl: {
    zIndex: 1,
    position: 'absolute',
    top: '-10px',
    right: '0px',
    margin: '0px',
    minWidth: 120
  },
  menuItem: {
    color: 'black'
  }
}));

export default function CustomizationMenu() {
  const classes = useStyles();
  const [color, setColor] = React.useState('');
  const [open, setOpen] = React.useState(false);

  const handleChange = (event) => {
    setColor(event.target.value);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleOpen = () => {
    setOpen(true);
  };

  return (
    <div>
      <FormControl className={classes.formControl}>
        <InputLabel id="demo-controlled-open-select-label">Color</InputLabel>
        <Select
          labelId="demo-controlled-open-select-label"
          id="demo-controlled-open-select"
          open={open}
          onClose={handleClose}
          onOpen={handleOpen}
          value={color}
          onChange={handleChange}
        >
          <MenuItem value="">
            <em>None</em>
          </MenuItem>
          <MenuItem className={classes.menuItem} value={10}>Option A</MenuItem>
          <MenuItem className={classes.menuItem} value={20}>Option B</MenuItem>
          <MenuItem className={classes.menuItem} value={30}>Option C</MenuItem>
        </Select>
      </FormControl>
    </div>
  );
}